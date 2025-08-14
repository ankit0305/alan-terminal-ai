#!/usr/bin/env python3
"""
Alan - Terminal Command Assistant using Ollama
Usage: alan please [your request]
Example: alan please list directory files
"""

import subprocess
import sys
import os
import time

def check_ollama():
    """Check if Ollama is running and accessible."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def get_command_from_ollama(user_request, model):
    """Get a terminal command suggestion from Ollama."""
    prompt = f"""Generate only the terminal command for: {user_request}

Return ONLY the command, no explanations or formatting."""

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
                    if line and not line.startswith(('Request:', 'Command:', 'Generate', 'Return')):
                        return line
            return lines[0] if lines else None
        
        # If generate doesn't work, try run
        result = subprocess.run([
            'ollama', 'run', model, prompt
            # '--think=false',
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            command = result.stdout.strip()
            lines = [line.strip() for line in command.split('\n') if line.strip()]
            if lines:
                for line in lines:
                    line = line.replace('`', '').strip()
                    if line and not line.startswith(('Request:', 'Command:', 'Generate', 'Return')):
                        return line
            return lines[0] if lines else None
            
        return None
        
    except subprocess.TimeoutExpired:
        print("⚠️  Ollama request timed out", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  Error communicating with Ollama: {e}", file=sys.stderr)
        return None

def is_safe_command(command):
    """Basic safety check for commands."""
    dangerous_patterns = [
        'rm -rf /', 'sudo rm -rf', 'format', 'mkfs', 'fdisk',
        'dd if=', '> /dev/', 'chmod 777 /', 'chown root /',
        'killall -9', 'pkill -9', 'reboot', 'shutdown'
    ]
    
    command_lower = command.lower()
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return False
    return True

def execute_command(command):
    """Execute the command safely."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.stdout:
            print(result.stdout.rstrip())
        
        if result.stderr and result.returncode != 0:
            print(f"Error: {result.stderr.rstrip()}", file=sys.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⚠️  Command timed out", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  Error executing command: {e}", file=sys.stderr)
        return False

def show_help():
    """Show help message."""
    help_text = """
🤖 Alan - Your Terminal Assistant

Usage:
  alan please [your request]

Examples:
  alan please list directory files
  alan please show current directory
  alan please find files with .txt extension
  alan please show disk usage
  alan please check running processes

Options:
  alan --help    Show this help message
  alan --version Show version information
    """
    print(help_text)

def main():
    if len(sys.argv) < 2:
        print("Usage: alan please [your request]")
        print("Try: alan --help for more information")
        sys.exit(1)
    
    # Handle help and version
    if sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
        sys.exit(0)
    
    if sys.argv[1] in ['--version', '-v']:
        print("Alan Terminal Assistant v1.0")
        sys.exit(0)
    
    # Check if first argument is "please"
    if sys.argv[1].lower() != 'please':
        print("Please start your request with 'please'")
        print("Example: alan please list directory files")
        sys.exit(1)
    
    # Get the user request (everything after "please")
    if len(sys.argv) < 3:
        print("Please provide a request after 'please'")
        print("Example: alan please list directory files")
        sys.exit(1)
    
    user_request = ' '.join(sys.argv[2:])
    
    # Check if Ollama is available
    if not check_ollama():
        print("❌ Ollama is not running or not installed.", file=sys.stderr)
        print("Please install Ollama and run 'ollama serve'", file=sys.stderr)
        sys.exit(1)
    
    # Get command from Ollama - try different models
    # Try models in order of preference
    models_to_try = ['qwen2.5:0.5b']
    # ["llama3.2", "gemma3:270m", "codellama", "mistral"]
    model = None
    
    # Check which models are available
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        available_models = result.stdout.lower()
        
        for m in models_to_try:
            if m in available_models:
                model = m
                break
    except:
        model = "gemma3:270m"  # fallback
    
    if not model:
        print("❌ No compatible models found. Please install a model:", file=sys.stderr)
        print(f"ollama pull {model}", file=sys.stderr)
        sys.exit(1)
    print(f"🔍 Using model: {model}")
    suggested_command = get_command_from_ollama(user_request, model)
    
    if not suggested_command:
        print("❌ Could not get a command suggestion.", file=sys.stderr)
        sys.exit(1)
    
    print(f"💡 Suggested: {suggested_command}")
    
    # Safety check
    if not is_safe_command(suggested_command):
        print("⚠️  This command appears potentially dangerous.", file=sys.stderr)
        print("Please review and run manually if needed.", file=sys.stderr)
        sys.exit(1)
    
    # Ask for confirmation
    try:
        choice = input("Execute? [y/N]: ").lower().strip()
        
        if choice in ['y', 'yes']:
            print(f"⚡ Running: {suggested_command}")
            print("-" * 40)
            execute_command(suggested_command)
        else:
            print("❌ Cancelled")
            
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        sys.exit(1)

if __name__ == "__main__":
    main()