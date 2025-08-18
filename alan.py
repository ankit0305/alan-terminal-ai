#!/usr/bin/env python3
"""
Alan - Terminal Command Assistant using Ollama
Usage: alan please [your request]
Example: alan please list directory files
"""

import subprocess
import sys

from alan_assistant import AlanAssistant


def main():
    alan = AlanAssistant()

    if len(sys.argv) < 2:
        print("Usage: alan please [your request]")
        print("       alan copy [command]")
        print("Try: alan --help for more information")
        sys.exit(1)

    # Get the user request (everything after "please")
    if len(sys.argv) < 4:
        print("Please provide a request after 'please'")
        print("Example: alan please list directory files")
        sys.exit(1)

    # Handle special commands that don't use "please"
    if sys.argv[3].lower() == "copy":
        # copy_args = sys.argv[2:] if len(sys.argv) > 2 else None
        alan.handle_copy_command()
        sys.exit(0)

    # Handle help and version (check both first argument and second argument)
    help_commands = ["--help", "-h", "help"]
    version_commands = ["--version", "-v"]

    if sys.argv[3] in help_commands:
        alan.show_help()
        sys.exit(0)
    elif sys.argv[3] in version_commands:
        print(f"Alan Terminal Assistant v1.0 - Running on {alan.os_info['name']}")
        sys.exit(0)

    # Check if first argument is "alan please"
    if sys.argv[1].lower() != "alan" and sys.argv[2].lower() != "please":
        print("Please start your request with 'alan please'")
        print("Example: alan please list directory files")
        print("Or use: alan copy [command]")
        print("For help: alan --help or alan please --help")
        sys.exit(1)

    user_request = " ".join(sys.argv[3:])
    print(user_request)

    # Show system info
    print(f"🖥️  System: {alan.os_info['name']} ({alan.os_info['type']})")

    # Check if Ollama is available
    if not alan.check_ollama():
        print("❌ Ollama is not running or not installed.", file=sys.stderr)
        print("Please install Ollama and run 'ollama serve'", file=sys.stderr)
        sys.exit(1)

    # Try models in order of preference
    models_to_try = ["qwen2.5:0.5b", "llama3.2", "gemma3:270m", "codellama", "mistral"]
    model = None

    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        available_models = result.stdout.lower()

        for m in models_to_try:
            if m in available_models:
                model = m
                break
    except:
        model = "qwen2.5:0.5b"  # fallback

    if not model:
        print("❌ No compatible models found. Please install a model:", file=sys.stderr)
        print(f"ollama pull qwen2.5:0.5b", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Using model: {model}")
    suggested_command = alan.get_command_from_ollama(user_request, model)

    if not suggested_command:
        print("❌ Could not get a command suggestion.", file=sys.stderr)
        sys.exit(1)

    print(f"💡 Suggested ({alan.os_info['name']}): {suggested_command}")

    # Safety check
    if not alan.is_safe_command(suggested_command):
        print("⚠️  This command appears potentially dangerous.", file=sys.stderr)
        print("Please review and run manually if needed.", file=sys.stderr)
        sys.exit(1)

    try:
        choice = input("Execute? [y/N]: ").lower().strip()

        if choice in ["y", "yes"]:
            with open("output.txt", "a") as file:
                file.write(str(suggested_command) + "\n")
            print(f"⚡ Running: {suggested_command}")
            print("-" * 40)
            alan.execute_command(suggested_command)
            print("-" * 40)
            print("💡 Tip: Use 'alan copy' to copy the output to clipboard")
        else:
            print("❌ Cancelled")

    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()
