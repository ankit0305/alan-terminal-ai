````markdown
# 🖥️ Alan – Terminal Command Assistant (Powered by Ollama)

Alan is your friendly AI-powered terminal assistant that turns natural language requests into safe, executable shell commands using [Ollama](https://ollama.ai/).

---

## 🚀 Features

- **Natural language to terminal commands**  
  Example: `alan please list directory files` → `ls`
- **Safety checks** for dangerous commands  
- **Supports multiple Ollama models**  
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
```

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

* **Default model:** Change the `models_to_try` list in the script to use your preferred Ollama models.
* **Dangerous commands list:** Update `dangerous_patterns` in the `is_safe_command()` function.
