import subprocess
import sys
import platform
from alan_config import AlanConfig

class AlanAssistant:
    def __init__(self):
        self.config = AlanConfig()
        self.last_command = None
        self.last_output = None
        self.clipboard_content = None
        self.os_info = self.detect_system()

    def detect_system(self):
        """Detect the current operating system and return relevant info."""
        system = platform.system().lower()
        
        if system == 'darwin':
            return {
                'name': 'macOS',
                'type': 'unix',
                'package_manager': 'brew',
                'shell': 'bash/zsh'
            }
        elif system == 'linux':
            # Try to detect Linux distribution
            distro = 'Linux'
            package_manager = 'apt'  # default
            
            try:
                # Check for different package managers
                if subprocess.run(['which', 'apt'], capture_output=True).returncode == 0:
                    package_manager = 'apt'
                elif subprocess.run(['which', 'yum'], capture_output=True).returncode == 0:
                    package_manager = 'yum'
                elif subprocess.run(['which', 'dnf'], capture_output=True).returncode == 0:
                    package_manager = 'dnf'
                elif subprocess.run(['which', 'pacman'], capture_output=True).returncode == 0:
                    package_manager = 'pacman'
                elif subprocess.run(['which', 'zypper'], capture_output=True).returncode == 0:
                    package_manager = 'zypper'
            except:
                pass
                
            return {
                'name': distro,
                'type': 'unix',
                'package_manager': package_manager,
                'shell': 'bash'
            }
        elif system == 'windows':
            return {
                'name': 'Windows',
                'type': 'windows',
                'package_manager': 'chocolatey/winget',
                'shell': 'powershell/cmd'
            }
        else:
            return {
                'name': 'Unknown',
                'type': 'unknown',
                'package_manager': 'unknown',
                'shell': 'unknown'
            }

    def check_ollama(self):
        """Check if Ollama is running and accessible."""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_command_from_ollama(self, user_request, model):
        """Get a terminal command suggestion from Ollama with system context."""
        
        # Create system-specific prompt
        system_context = f"""
System: {self.os_info['name']} ({self.os_info['type']})
"""
# Package Manager: {self.os_info['package_manager']}
# Shell: {self.os_info['shell']}
        
        prompt = f"""{system_context}

Generate ONLY the terminal command for {self.os_info['name']} system for: {user_request}

Important:
- Return ONLY the command that works on {self.os_info['name']}
- No explanations, just the command
- Make it {self.os_info['name']}-specific

Command:"""
# - Use {self.os_info['package_manager']} for package management if needed
        try:
            # Try the generate command first
            result = subprocess.run([
                'ollama', 'generate', model, prompt
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                command = result.stdout.strip()
                # Clean up the response
                lines = [line.strip() for line in command.split('\n') if line.strip()]
                if lines:
                    # Get the first non-empty line that looks like a command
                    for line in lines:
                        line = line.replace('`', '').strip()
                        if line and not line.startswith(('Request:', 'Command:', 'Generate', 'Return', 'System:')):
                            return line
                return lines[0] if lines else None
            
            # If generate doesn't work, try run
            result = subprocess.run([
                'ollama', 'run', model, prompt
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                command = result.stdout.strip()
                lines = [line.strip() for line in command.split('\n') if line.strip()]
                if lines:
                    for line in lines:
                        line = line.replace('`', '').strip()
                        if line and not line.startswith(('Request:', 'Command:', 'Generate', 'Return', 'System:')):
                            return line
                return lines[0] if lines else None
                
            return None
            
        except subprocess.TimeoutExpired:
            print("⚠️  Ollama request timed out", file=sys.stderr)
            return None
        except Exception as e:
            print(f"⚠️  Error communicating with Ollama: {e}", file=sys.stderr)
            return None

    def is_safe_command(self, command):
        """System-aware safety check for commands."""
        # Common dangerous patterns across all systems
        dangerous_patterns = [
            'rm -rf /', 'sudo rm -rf', 'format', 'mkfs', 'fdisk',
            'dd if=', '> /dev/', 'chmod 777 /', 'chown root /',
            'killall -9', 'pkill -9', 'reboot', 'shutdown'
        ]
        
        # Windows-specific dangerous patterns
        if self.os_info['type'] == 'windows':
            dangerous_patterns.extend([
                'format c:', 'del /f /s /q c:\\*', 'rmdir /s /q c:\\',
                'diskpart', 'reg delete', 'shutdown /s', 'shutdown /r'
            ])
        
        command_lower = command.lower()
        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return False
        return True

    def execute_command(self, command):
        """Execute the command safely with system-specific handling."""
        try:
            # Use appropriate shell based on system
            if self.os_info['type'] == 'windows':
                # On Windows, use shell=True with cmd
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            else:
                # On Unix-like systems
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            output = ""
            if result.stdout:
                output = result.stdout.rstrip()
                print(output)
                self.last_output = output
            
            if result.stderr and result.returncode != 0:
                error_output = result.stderr.rstrip()
                print(f"Error: {error_output}", file=sys.stderr)
                
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print("⚠️  Command timed out", file=sys.stderr)
            return False
        except Exception as e:
            print(f"⚠️  Error executing command: {e}", file=sys.stderr)
            return False

    def handle_copy_command(self, copy_args=None):
        """Copy last output or run command and copy its output to clipboard."""
        
        # If no arguments provided, read last line from output.txt
        if not copy_args:
            try:
                with open("output.txt", "r", encoding="utf-8") as file:
                    lines = file.readlines()
                    
                if not lines:
                    print("❌ No output found in output.txt")
                    print("💡 Usage: 'alan copy [command]' to run and copy a command")
                    return False
                
                # Get the last non-empty line
                last_line = None
                for line in reversed(lines):
                    stripped_line = line.strip()
                    if stripped_line:  # Skip empty lines
                        last_line = stripped_line
                        break
                
                if not last_line:
                    print("❌ No non-empty output found in output.txt")
                    return False
                    
                return self._copy_to_clipboard(last_line, "Last output from file")
                
            except FileNotFoundError:
                print("❌ output.txt file not found")
                print("💡 Usage: 'alan please copy [command]' to run and copy a command")
                return False
            except Exception as e:
                print(f"⚠️  Error reading output.txt: {e}")
                return False
        
        # If arguments provided, run the command and copy its output
        command = ' '.join(copy_args)
        print(f"⚡ Running and copying: {command}")
        
        try:
            if self.os_info['type'] == 'windows':
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            else:
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            
            output = ""
            if result.stdout:
                output = result.stdout.rstrip()
                print(output)
            
            if result.stderr and result.returncode != 0:
                error_output = result.stderr.rstrip()
                print(f"Error: {error_output}", file=sys.stderr)
                output += f"\nError: {error_output}"
                
            if output:
                return self._copy_to_clipboard(output, f"Output of '{command}'")
            else:
                print("❌ No output to copy")
                return False
                
        except subprocess.TimeoutExpired:
            print("⚠️  Command timed out", file=sys.stderr)
            return False
        except Exception as e:
            print(f"⚠️  Error executing command: {e}", file=sys.stderr)
            return False

    def _copy_to_clipboard(self, content, description="Content"):
        """Helper method to copy content to clipboard with system-specific commands."""
        try:
            if self.os_info['name'] == 'macOS':
                process = subprocess.run(['pbcopy'], input=content, text=True)
                success = process.returncode == 0
            elif self.os_info['type'] == 'linux':
                # Try xclip first, then xsel
                try:
                    process = subprocess.run(['xclip', '-selection', 'clipboard'], 
                                           input=content, text=True)
                    success = process.returncode == 0
                    if not success:
                        raise Exception("xclip failed")
                except:
                    try:
                        process = subprocess.run(['xsel', '--clipboard', '--input'], 
                                               input=content, text=True)
                        success = process.returncode == 0
                        if not success:
                            print("❌ No clipboard tool found (install xclip or xsel)")
                            return False
                    except:
                        print("❌ No clipboard tool found (install xclip or xsel)")
                        return False
            elif self.os_info['type'] == 'windows':
                process = subprocess.run(['clip'], input=content, text=True, shell=True)
                success = process.returncode == 0
            else:
                print("❌ Clipboard not supported on this system")
                return False
            
            if success:
                print(f"✅ {description} copied to clipboard")
                return True
            else:
                print("❌ Failed to copy to clipboard")
                return False
                
        except Exception as e:
            print(f"❌ Clipboard error: {e}")
            return False

    def show_help(self):
        """Show help message with system-specific information."""
        help_text = f"""
🤖 Alan - Your Terminal Assistant

System: {self.os_info['name']} ({self.os_info['type']})
Package Manager: {self.os_info['package_manager']}

Usage:
alan please [your request]        Generate and run AI-suggested commands
alan copy                         Copy last Alan command output
alan copy [command]               Run command and copy its output

Examples:
alan please list directory files
alan please show current directory  
alan please find files with .txt extension
alan please show disk usage
alan please check running processes
alan please install python package requests

alan copy                         # Copy last Alan output
alan copy df -h                   # Run 'df -h' and copy output
alan copy ls -la                  # Run 'ls -la' and copy output

Options:
alan --help    Show this help message
alan --version Show version information

Note: Commands will be generated specifically for your {self.os_info['name']} system.
        """
        print(help_text)