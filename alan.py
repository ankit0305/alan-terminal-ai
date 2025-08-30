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
    """
    main function
    """
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
    elif sys.argv[3].lower() == "stats":
        alan.show_tracking_statistics()
        sys.exit(0)

    # Handle help and version (check both first argument and second argument)
    help_commands = ["--help", "-h", "help"]
    version_commands = ["--version", "-v"]

    if sys.argv[3] in help_commands:
        alan.show_help()
        sys.exit(0)
    elif sys.argv[3] in version_commands:
        print(
            f"Alan Terminal Assistant v1.0 - Running on {alan.os_info['name']}"
        )
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
    models_to_try = [
        "gemma3:4b",
        "qwen2.5:0.5b",
        "llama3.2",
        "gemma3:270m",
        "codellama",
        "mistral",
    ]
    model = None

    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, check=False, text=True
        )
        available_models = result.stdout.lower()

        for m in models_to_try:
            if m in available_models:
                model = m
                break
    except Exception:
        model = "qwen2.5:0.5b"  # fallback

    if not model:
        print(
            "❌ No compatible models found. Please install a model:",
            file=sys.stderr,
        )
        print("ollama pull qwen2.5:0.5b", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Using model: {model}")

    # First, check if this is a multistep operation
    if alan.handle_multistep_request(user_request):
        # Multistep operation was handled successfully
        print(
            "💡 Tip: Use 'alan copy' to copy the operation summary to clipboard"
        )
        sys.exit(0)

    # If not a multistep operation, proceed with regular single command approach
    suggested_command = alan.get_command_from_ollama(user_request, model)

    if not suggested_command:
        print("❌ Could not get a command suggestion.", file=sys.stderr)
        sys.exit(1)

    # Track the command suggestion
    tracking_id = alan.track_command_suggestion(
        user_request, suggested_command, model
    )

    # Get insights for this command
    insights = alan.get_command_insights(user_request, suggested_command)

    print(
        f"\033[1;37;44m💡 Suggested ({alan.os_info['name']}): {suggested_command}\033[0m"
    )

    # Show confidence score if available
    if insights["confidence_score"] != 0.5:  # Not default
        confidence_percent = insights["confidence_score"] * 100
        if confidence_percent > 80:
            print(f"🎯 High confidence ({confidence_percent:.0f}%)")
        elif confidence_percent < 30:
            print(f"⚠️  Low confidence ({confidence_percent:.0f}%)")
        else:
            print(f"📊 Confidence: {confidence_percent:.0f}%")

    # Show similar accepted commands if available
    if insights["similar_accepted_commands"]:
        print("💭 Similar commands you've accepted:")
        for similar in insights["similar_accepted_commands"][:2]:
            print(f"   • {similar['command']}")

    # Safety check
    if not alan.is_safe_command(suggested_command):
        print("⚠️  This command appears potentially dangerous.", file=sys.stderr)
        print("Please review and run manually if needed.", file=sys.stderr)
        alan.track_user_decision(False, "Command flagged as dangerous")
        sys.exit(1)

    try:
        choice = input("Execute? [y/N]: ").lower().strip()

        if choice in ["y", "yes"]:
            # Track user acceptance
            alan.track_user_decision(True)

            with open("output.txt", "a") as file:
                file.write(str(suggested_command) + "\n")
            print(f"⚡ Running: {suggested_command}")
            print("-" * 40)

            # Execute and track result
            success = alan.execute_command(suggested_command)
            alan.track_execution_result(success, alan.last_output)

            print("-" * 40)
            print("💡 Tip: Use 'alan copy' to copy the output to clipboard")

            if success:
                print("✅ Command executed successfully")
            else:
                print("❌ Command execution failed")

        else:
            # Track user rejection
            alan.track_user_decision(False)
            print("❌ Cancelled")

    except KeyboardInterrupt:
        # Track user cancellation
        alan.track_user_decision(False, "User cancelled with Ctrl+C")
        print("\n❌ Cancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()
