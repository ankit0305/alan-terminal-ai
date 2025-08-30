"""
Multi-step operation handler for Alan Terminal Assistant
Handles complex operations that require multiple commands with state management
"""

import os
import re
import subprocess
from typing import Dict, List


class MultiStepOperation:
    """
    Handles multi-step terminal operations with proper state management
    """

    def __init__(self, os_info: Dict):
        """
        Initialize with system information
        """
        self.os_info = os_info
        self.current_directory = os.getcwd()
        self.operation_history = []
        self.failed_steps = []

    def detect_multistep_operation(self, user_request: str) -> bool:
        """
        Detect if a user request requires multiple steps
        """
        multistep_patterns = [
            # Directory creation + navigation patterns
            r"create.*(?:directory|folder|dir).*(?:and|then).*(?:cd|go|navigate|enter)",
            r"(?:mkdir|create dir).*(?:and|then).*(?:cd|go into|navigate)",
            # Git operations
            r"create.*(?:directory|folder|dir).*(?:and|then).*(?:git|initialize|init)",
            r"(?:mkdir|create dir).*(?:and|then).*(?:git init|initialize git)",
            r"(?:clone|git clone).*(?:and|then).*(?:cd|go|navigate)",
            # Project setup patterns
            r"create.*project.*(?:and|then).*(?:initialize|init|setup)",
            r"(?:setup|create).*(?:and|then).*(?:install|npm|pip|yarn)",
            # File operations + actions
            r"create.*file.*(?:and|then).*(?:edit|open|write)",
            r"(?:touch|create).*(?:and|then).*(?:echo|write|edit)",
            # Build/compile patterns
            r"(?:build|compile|make).*(?:and|then).*(?:run|execute|start)",
            # Multiple command indicators
            r"(?:first|then|next|after|finally)",
            r"(?:and then|followed by|after that)",
            r"(?:step \d+|1\.|2\.|3\.)",
        ]

        user_request_lower = user_request.lower()

        for pattern in multistep_patterns:
            if re.search(pattern, user_request_lower):
                return True

        # Check for explicit command chaining
        if (
            " && " in user_request
            or " ; " in user_request
            or " | " in user_request
        ):
            return True

        return False

    def parse_multistep_request(self, user_request: str) -> List[Dict]:
        """
        Parse a multistep request into individual operations
        """
        steps = []

        # Handle explicit command chaining first
        if " && " in user_request:
            commands = user_request.split(" && ")
            for cmd in commands:
                steps.append(
                    {
                        "type": "command",
                        "command": cmd.strip(),
                        "description": f"Execute: {cmd.strip()}",
                    }
                )
            return steps

        # Handle common patterns
        user_request_lower = user_request.lower()

        # Pattern: Create directory and initialize git
        if re.search(
            r"create.*(?:directory|folder|dir).*(?:and|then).*(?:git|initialize|init)",
            user_request_lower,
        ):
            # Extract directory name
            dir_match = re.search(
                r'(?:create|mkdir).*?(?:directory|folder|dir).*?(?:called|named)?\s*["\']?([a-zA-Z0-9_-]+)["\']?',
                user_request_lower,
            )
            if dir_match:
                dir_name = dir_match.group(1)
                steps.extend(
                    [
                        {
                            "type": "command",
                            "command": (
                                f"mkdir -p {dir_name}"
                                if self.os_info["type"] != "windows"
                                else f"mkdir {dir_name}"
                            ),
                            "description": f"Create directory: {dir_name}",
                        },
                        {
                            "type": "cd",
                            "directory": dir_name,
                            "description": f"Navigate to directory: {dir_name}",
                        },
                        {
                            "type": "command",
                            "command": "git init",
                            "description": "Initialize git repository",
                        },
                    ]
                )

        # Pattern: Clone and navigate
        elif re.search(
            r"(?:clone|git clone).*(?:and|then).*(?:cd|go|navigate)",
            user_request_lower,
        ):
            # Extract git URL and directory name
            clone_match = re.search(
                r"(?:git\s+)?clone\s+([^\s]+)", user_request
            )
            if clone_match:
                repo_url = clone_match.group(1)
                # Extract repo name from URL
                repo_name = repo_url.split("/")[-1].replace(".git", "")
                steps.extend(
                    [
                        {
                            "type": "command",
                            "command": f"git clone {repo_url}",
                            "description": f"Clone repository: {repo_url}",
                        },
                        {
                            "type": "cd",
                            "directory": repo_name,
                            "description": f"Navigate to cloned repository: {repo_name}",
                        },
                    ]
                )

        # Pattern: Create project and setup
        elif re.search(
            r"create.*project.*(?:and|then).*(?:initialize|init|setup)",
            user_request_lower,
        ):
            # Extract project name
            project_match = re.search(
                r'(?:create|make).*?project.*?(?:called|named)?\s*["\']?([a-zA-Z0-9_-]+)["\']?',
                user_request_lower,
            )
            if project_match:
                project_name = project_match.group(1)
                steps.extend(
                    [
                        {
                            "type": "command",
                            "command": (
                                f"mkdir -p {project_name}"
                                if self.os_info["type"] != "windows"
                                else f"mkdir {project_name}"
                            ),
                            "description": f"Create project directory: {project_name}",
                        },
                        {
                            "type": "cd",
                            "directory": project_name,
                            "description": f"Navigate to project directory: {project_name}",
                        },
                    ]
                )

                # Add initialization based on project type
                if "npm" in user_request_lower or "node" in user_request_lower:
                    steps.append(
                        {
                            "type": "command",
                            "command": "npm init -y",
                            "description": "Initialize npm project",
                        }
                    )
                elif (
                    "python" in user_request_lower
                    or "pip" in user_request_lower
                ):
                    steps.extend(
                        [
                            {
                                "type": "command",
                                "command": (
                                    "python -m venv venv"
                                    if self.os_info["type"] != "windows"
                                    else "python -m venv venv"
                                ),
                                "description": "Create Python virtual environment",
                            },
                            {
                                "type": "command",
                                "command": "touch requirements.txt",
                                "description": "Create requirements.txt file",
                            },
                        ]
                    )

        # Pattern: Create file and edit
        elif re.search(
            r"create.*file.*(?:and|then).*(?:edit|open|write)",
            user_request_lower,
        ):
            file_match = re.search(
                r'(?:create|touch).*?file.*?(?:called|named)?\s*["\']?([a-zA-Z0-9_.-]+)["\']?',
                user_request_lower,
            )
            if file_match:
                filename = file_match.group(1)
                steps.extend(
                    [
                        {
                            "type": "command",
                            "command": (
                                f"touch {filename}"
                                if self.os_info["type"] != "windows"
                                else f"type nul > {filename}"
                            ),
                            "description": f"Create file: {filename}",
                        },
                        {
                            "type": "command",
                            "command": (
                                f"code {filename}"
                                if self.os_info["type"] != "windows"
                                else f"notepad {filename}"
                            ),
                            "description": f"Open file for editing: {filename}",
                        },
                    ]
                )

        # If no specific pattern matched, try to break down by common separators
        if not steps:
            separators = [
                " and then ",
                " then ",
                " and ",
                " after that ",
                " followed by ",
            ]
            current_text = user_request

            for separator in separators:
                if separator in current_text.lower():
                    parts = re.split(
                        separator, current_text, flags=re.IGNORECASE
                    )
                    for part in parts:
                        part = part.strip()
                        if part:
                            steps.append(
                                {
                                    "type": "command",
                                    "command": part,
                                    "description": f"Execute: {part}",
                                }
                            )
                    break

        return steps

    def execute_multistep_operation(self, steps: List[Dict]) -> bool:
        """
        Execute a series of steps with proper state management
        """
        print(f"🔄 Executing {len(steps)} step operation...")
        print("-" * 50)

        self.current_directory
        success = True

        for i, step in enumerate(steps, 1):
            print(f"Step {i}/{len(steps)}: {step['description']}")

            try:
                if step["type"] == "cd":
                    success = self._change_directory(step["directory"])
                elif step["type"] == "command":
                    success = self._execute_single_command(step["command"])
                else:
                    print(f"⚠️  Unknown step type: {step['type']}")
                    success = False

                if not success:
                    print(f"❌ Step {i} failed: {step['description']}")
                    self.failed_steps.append((i, step))
                    break
                else:
                    print(f"✅ Step {i} completed successfully")
                    self.operation_history.append((i, step))

            except Exception as e:
                print(f"❌ Step {i} failed with error: {e}")
                self.failed_steps.append((i, step))
                success = False
                break

            print()

        print("-" * 50)

        if success:
            print(f"🎉 All {len(steps)} steps completed successfully!")
        else:
            print(
                f"⚠️  Operation failed at step {len(self.operation_history) + 1}"
            )
            print("💡 You can retry the failed steps manually")

        return success

    def _change_directory(self, directory: str) -> bool:
        """
        Change the current working directory
        """
        try:
            # Handle relative and absolute paths
            if os.path.isabs(directory):
                target_dir = directory
            else:
                target_dir = os.path.join(self.current_directory, directory)

            # Check if directory exists
            if not os.path.exists(target_dir):
                print(f"❌ Directory does not exist: {target_dir}")
                return False

            if not os.path.isdir(target_dir):
                print(f"❌ Path is not a directory: {target_dir}")
                return False

            # Change directory
            os.chdir(target_dir)
            self.current_directory = os.getcwd()
            print(f"📁 Changed directory to: {self.current_directory}")
            return True

        except Exception as e:
            print(f"❌ Failed to change directory: {e}")
            return False

    def _execute_single_command(self, command: str) -> bool:
        """
        Execute a single command in the current directory context
        """
        try:
            # Use appropriate shell based on system
            if self.os_info["type"] == "windows":
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=30,
                    cwd=self.current_directory,
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    check=False,
                    text=True,
                    timeout=30,
                    cwd=self.current_directory,
                )

            output = ""
            if result.stdout:
                output = result.stdout.rstrip()
                if output:
                    print(f"📤 Output: {output}")

            if result.stderr and result.returncode != 0:
                error_output = result.stderr.rstrip()
                print(f"❌ Error: {error_output}")
                return False

            return result.returncode == 0

        except subprocess.TimeoutExpired:
            print("⚠️  Command timed out")
            return False
        except Exception as e:
            print(f"⚠️  Error executing command: {e}")
            return False

    def get_operation_summary(self) -> str:
        """
        Get a summary of the completed operation
        """
        if not self.operation_history and not self.failed_steps:
            return "No operations executed"

        summary = []
        summary.append(f"Operation Summary:")
        summary.append(f"- Completed steps: {len(self.operation_history)}")
        summary.append(f"- Failed steps: {len(self.failed_steps)}")
        summary.append(f"- Current directory: {self.current_directory}")

        if self.failed_steps:
            summary.append("\nFailed steps:")
            for step_num, step in self.failed_steps:
                summary.append(f"  {step_num}. {step['description']}")

        return "\n".join(summary)

    def reset_state(self):
        """
        Reset the operation state
        """
        self.current_directory = os.getcwd()
        self.operation_history.clear()
        self.failed_steps.clear()
