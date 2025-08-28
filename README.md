````markdown
# 🖥️ Alan – Terminal Command Assistant (Powered by Ollama)

Alan is your friendly AI-powered terminal assistant that turns natural language requests into safe, executable shell commands using [Ollama](https://ollama.ai/).

---

## 🚀 Features

- **Natural language to terminal commands**  
  Example: `alan please list directory files` → `ls`
- **Smart command tracking and learning**  
  Alan learns from your preferences to improve suggestions
- **Confidence scoring** for command suggestions
- **Safety checks** for dangerous commands  
- **Supports multiple Ollama models**  
- **Multi-step operation support**
- **Command statistics and insights**
- **Confirmation before execution**

---

## 📦 Requirements

- **Python 3.7+**
- [Ollama](https://ollama.ai/) installed and running  
  ```bash
  brew install ollama
  ollama serve
````

* At least one supported Ollama model (default: `qwen2.5:0.5b`)

  ```bash
  ollama pull qwen2.5:0.5b
  ```

---

## 🔧 Installation

1. **Download the `alan` script**

   ```bash
   curl -O https://raw.githubusercontent.com/ankit0305/alan/main/alan
   chmod +x alan
   ```

2. **Move to your local bin directory**

   ```bash
   mkdir -p ~/.local/bin
   mv alan ~/.local/bin/
   ```

3. **Add to your PATH** (if not already)

   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

   *(Use `.bashrc` if you're on bash)*

---

## 💡 Usage

```bash
alan please [your request]
python3 alan.py please list directory files
```

### Examples

```bash
alan please list directory files
alan please show current directory
alan please find files with .txt extension
alan please show disk usage
alan please check running processes
```

---

## 📜 Options

```bash
alan --help     # Show help message
alan --version  # Show version info
alan stats      # Show command tracking statistics
```

---

## 🧠 Smart Learning & Tracking

Alan automatically tracks your command preferences to improve future suggestions:

### Command Tracking Features
- **Acceptance/Rejection Tracking**: Learns which commands you accept or reject
- **Confidence Scoring**: Shows confidence levels for suggestions based on your history
- **Similar Command Suggestions**: Shows previously accepted similar commands
- **Usage Statistics**: Track your most used command types and success rates
- **Pattern Analysis**: Identifies patterns in your command preferences

### View Your Statistics
```bash
alan stats
```

This shows:
- Total suggestions made
- Acceptance rate percentage
- Most used command types
- Recent activity summary
- Actionable insights for improvement

### Data Storage
- Command history is stored in `command_history.json`
- Data includes timestamps, user requests, suggested commands, and outcomes
- Automatic cleanup of old data (configurable)
- Export functionality for data analysis

---

## ⚠️ Safety

Alan will:

* Reject dangerous commands (e.g., `rm -rf /`)
* Ask for confirmation before running anything
* Display the suggested command first

You can review and modify the command before running it.

## 🛠 How It Works

1. You type a natural language request with `alan please`.
2. Alan sends the request to your local Ollama instance.
3. The AI model returns a **single shell command**.
4. Alan checks if it’s safe and asks for your confirmation.
5. If approved, it runs the command and shows the output.

## 🧩 Customization

### Configuration File
Create `~/.alan_config.json` to customize Alan's behavior:

```json
{
  "tracking": {
    "enabled": true,
    "show_confidence": true,
    "show_similar_commands": true
  },
  "display": {
    "show_system_info": true,
    "use_emojis": true,
    "verbose_output": false
  },
  "safety": {
    "enable_safety_checks": true,
    "prompt_for_dangerous_commands": true
  }
}
```

### Advanced Customization
* **Default model:** Change the `models_to_try` list in the script to use your preferred Ollama models.
* **Dangerous commands list:** Update `dangerous_patterns` in the `is_safe_command()` function.
* **Tracking settings:** Adjust command tracking behavior in the config file.

---

## 📊 Example Output

When you use Alan, you'll see helpful information:

```bash
$ alan please list files
🖥️  System: macOS (unix)
🔍 Using model: gemma3:4b
💡 Suggested (macOS): ls -la
🎯 High confidence (85%)
💭 Similar commands you've accepted:
   • ls -l
Execute? [y/N]: y
⚡ Running: ls -la
----------------------------------------
total 48
drwxr-xr-x  8 user  staff   256 Jan 29 12:36 .
drwxr-xr-x  3 user  staff    96 Jan 29 12:30 ..
-rw-r--r--  1 user  staff  1234 Jan 29 12:35 alan.py
-rw-r--r--  1 user  staff   567 Jan 29 12:36 README.md
----------------------------------------
✅ Command executed successfully
💡 Tip: Use 'alan copy' to copy the output to clipboard
```
