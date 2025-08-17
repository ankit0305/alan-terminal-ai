import json
import sqlite3
from datetime import datetime
from pathlib import Path

class AlanConfig:
    def __init__(self):
        self.config_dir = Path.home() / '.alan'
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.history_db = self.config_dir / 'history.db'
        self.memory_file = self.config_dir / 'memory.json'
        self.favorites_file = self.config_dir / 'favorites.json'
        
        self.init_database()
        self.load_config()
    
    def init_database(self):
        """Initialize SQLite database for history."""
        conn = sqlite3.connect(self.history_db)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                request TEXT,
                command TEXT,
                executed BOOLEAN,
                success BOOLEAN,
                output TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def load_config(self):
        """Load configuration from file."""
        default_config = {
            'model': 'llama2',
            'safety_checks': True,
            'auto_confirm': False,
            'context_memory': True,
            'learning_mode': True,
            'output_format': 'standard'
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    self.config = {**default_config, **json.load(f)}
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def add_to_history(self, request, command, executed, success=None, output=None):
        """Add command to history."""
        conn = sqlite3.connect(self.history_db)
        conn.execute('''
            INSERT INTO command_history (timestamp, request, command, executed, success, output)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), request, command, executed, success, output))
        conn.commit()
        conn.close()
    
    def get_history(self, limit=20):
        """Get command history."""
        conn = sqlite3.connect(self.history_db)
        cursor = conn.execute('''
            SELECT timestamp, request, command, executed, success
            FROM command_history 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def load_memory(self):
        """Load context memory."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_memory(self, memory):
        """Save context memory."""
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=2)
    
    def load_favorites(self):
        """Load favorite commands."""
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_favorites(self, favorites):
        """Save favorite commands."""
        with open(self.favorites_file, 'w') as f:
            json.dump(favorites, f, indent=2)