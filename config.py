"""
Configuration settings for Alan Terminal Assistant
"""

import os
from typing import Any, Dict


class AlanConfig:
    """Configuration manager for Alan Terminal Assistant"""

    def __init__(self):
        """Initialize configuration with default values"""
        self.config = self._load_default_config()
        self._load_user_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration settings"""
        return {
            # Command tracking settings
            "tracking": {
                "enabled": True,
                "data_file": "command_history.json",
                "max_history_days": 30,
                "show_confidence": True,
                "show_similar_commands": True,
                "auto_cleanup_enabled": True,
                "export_on_exit": False,
            },
            # Display settings
            "display": {
                "show_system_info": True,
                "show_model_info": True,
                "show_insights": True,
                "use_emojis": True,
                "verbose_output": False,
            },
            # Safety settings
            "safety": {
                "enable_safety_checks": True,
                "prompt_for_dangerous_commands": True,
                "block_dangerous_commands": False,
                "custom_dangerous_patterns": [],
            },
            # Model preferences
            "models": {
                "preferred_models": [
                    "gemma3:4b",
                    "qwen2.5:0.5b",
                    "llama3.2",
                    "gemma3:270m",
                    "codellama",
                    "mistral",
                ],
                "fallback_model": "qwen2.5:0.5b",
                "timeout_seconds": 30,
            },
            # Advanced settings
            "advanced": {
                "enable_multistep": True,
                "max_command_length": 500,
                "enable_clipboard_integration": True,
                "debug_mode": False,
            },
        }

    def _load_user_config(self):
        """Load user-specific configuration if it exists"""
        config_file = os.path.expanduser("~/.alan_config.json")
        if os.path.exists(config_file):
            try:
                import json

                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    self._merge_config(user_config)
            except Exception as e:
                print(f"⚠️  Warning: Could not load user config: {e}")

    def _merge_config(self, user_config: Dict[str, Any]):
        """Merge user configuration with default configuration"""
        for section, settings in user_config.items():
            if section in self.config:
                if isinstance(settings, dict):
                    self.config[section].update(settings)
                else:
                    self.config[section] = settings
            else:
                self.config[section] = settings

    def get(self, section: str, key: str = None, default=None):
        """
        Get configuration value

        Args:
            section: Configuration section name
            key: Optional key within the section
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        if section not in self.config:
            return default

        if key is None:
            return self.config[section]

        return self.config[section].get(key, default)

    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value

        Args:
            section: Configuration section name
            key: Key within the section
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def is_enabled(self, section: str, key: str) -> bool:
        """
        Check if a feature is enabled

        Args:
            section: Configuration section name
            key: Key within the section

        Returns:
            True if enabled, False otherwise
        """
        return self.get(section, key, False)

    def save_user_config(self):
        """Save current configuration to user config file"""
        config_file = os.path.expanduser("~/.alan_config.json")
        try:
            import json

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"⚠️  Warning: Could not save user config: {e}")
            return False

    def create_sample_config(self):
        """Create a sample configuration file for users to customize"""
        sample_config = {
            "tracking": {
                "enabled": True,
                "show_confidence": True,
                "show_similar_commands": True,
            },
            "display": {
                "show_system_info": True,
                "use_emojis": True,
                "verbose_output": False,
            },
            "safety": {
                "enable_safety_checks": True,
                "prompt_for_dangerous_commands": True,
            },
        }

        sample_file = "alan_config_sample.json"
        try:
            import json

            with open(sample_file, "w", encoding="utf-8") as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            print(f"📝 Sample configuration created: {sample_file}")
            print("💡 Copy this to ~/.alan_config.json and customize as needed")
            return sample_file
        except Exception as e:
            print(f"⚠️  Could not create sample config: {e}")
            return None

    def show_current_config(self):
        """Display current configuration"""
        print("\n⚙️  Current Alan Configuration")
        print("=" * 40)

        for section, settings in self.config.items():
            print(f"\n[{section.upper()}]")
            if isinstance(settings, dict):
                for key, value in settings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {settings}")

        print("=" * 40)
        print("💡 To customize, create ~/.alan_config.json")


# Global configuration instance
config = AlanConfig()
