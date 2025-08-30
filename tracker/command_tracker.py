"""
Command tracking system for Alan Terminal Assistant
Tracks command acceptance/rejection patterns to improve future suggestions
"""

import hashlib
import json
import os
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List


class CommandTracker:
    """
    Tracks command suggestions and their acceptance/rejection patterns
    """

    def __init__(self, data_file: str = "command_history.json"):
        """
        Initialize the command tracker

        Args:
            data_file: Path to the JSON file storing command history
        """
        self.data_file = data_file
        self.history = self._load_history()
        self.session_commands = []

    def _load_history(self) -> Dict:
        """
        Load command history from file

        Returns:
            Dictionary containing command history data
        """
        if not os.path.exists(self.data_file):
            return {
                "commands": [],
                "patterns": {},
                "user_preferences": {},
                "statistics": {
                    "total_suggestions": 0,
                    "total_accepted": 0,
                    "total_rejected": 0,
                    "acceptance_rate": 0.0,
                },
            }

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: Could not load command history: {e}")
            return self._load_history()  # Return empty structure

    def _save_history(self):
        """
        Save command history to file
        """
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"⚠️  Warning: Could not save command history: {e}")

    def _generate_command_hash(self, command: str) -> str:
        """
        Generate a hash for a command to identify similar commands

        Args:
            command: The command string

        Returns:
            SHA256 hash of the normalized command
        """
        # Normalize command by removing extra spaces and converting to lowercase
        normalized = " ".join(command.lower().split())
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _extract_command_features(
        self, command: str, user_request: str
    ) -> Dict:
        """
        Extract features from a command for pattern analysis

        Args:
            command: The suggested command
            user_request: The original user request

        Returns:
            Dictionary of extracted features
        """
        features = {
            "command_length": len(command),
            "word_count": len(command.split()),
            "has_pipes": "|" in command,
            "has_redirects": ">" in command or "<" in command,
            "has_sudo": command.strip().startswith("sudo"),
            "has_flags": "-" in command,
            "command_type": command.split()[0] if command.split() else "",
            "request_length": len(user_request),
            "request_words": len(user_request.split()),
            "contains_file_ops": any(
                word in command.lower()
                for word in [
                    "ls",
                    "cat",
                    "grep",
                    "find",
                    "touch",
                    "mkdir",
                    "rm",
                ]
            ),
            "contains_system_ops": any(
                word in command.lower()
                for word in ["ps", "top", "kill", "systemctl", "service"]
            ),
            "contains_network_ops": any(
                word in command.lower()
                for word in ["curl", "wget", "ping", "ssh", "scp"]
            ),
            "contains_package_ops": any(
                word in command.lower()
                for word in ["apt", "yum", "brew", "pip", "npm"]
            ),
        }

        return features

    def track_suggestion(
        self,
        user_request: str,
        suggested_command: str,
        model_used: str,
        system_info: Dict,
    ) -> str:
        """
        Track a command suggestion

        Args:
            user_request: The original user request
            suggested_command: The command suggested by the AI
            model_used: The AI model that generated the suggestion
            system_info: System information (OS, etc.)

        Returns:
            Tracking ID for this suggestion
        """
        tracking_id = f"{int(time.time())}_{len(self.history['commands'])}"

        command_entry = {
            "tracking_id": tracking_id,
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "suggested_command": suggested_command,
            "command_hash": self._generate_command_hash(suggested_command),
            "model_used": model_used,
            "system_info": system_info,
            "features": self._extract_command_features(
                suggested_command, user_request
            ),
            "accepted": None,  # Will be updated when user responds
            "execution_success": None,  # Will be updated if command is executed
            "execution_output": None,
            "user_feedback": None,
        }

        self.history["commands"].append(command_entry)
        self.session_commands.append(tracking_id)
        self.history["statistics"]["total_suggestions"] += 1

        self._save_history()
        return tracking_id

    def track_user_decision(
        self, tracking_id: str, accepted: bool, user_feedback: str = None
    ):
        """
        Track user's decision on a command suggestion

        Args:
            tracking_id: The tracking ID of the suggestion
            accepted: Whether the user accepted the command
            user_feedback: Optional feedback from the user
        """
        for command in self.history["commands"]:
            if command["tracking_id"] == tracking_id:
                command["accepted"] = accepted
                command["user_feedback"] = user_feedback
                command["decision_timestamp"] = datetime.now().isoformat()

                # Update statistics
                if accepted:
                    self.history["statistics"]["total_accepted"] += 1
                else:
                    self.history["statistics"]["total_rejected"] += 1

                # Calculate acceptance rate
                total = self.history["statistics"]["total_suggestions"]
                accepted_count = self.history["statistics"]["total_accepted"]
                self.history["statistics"]["acceptance_rate"] = (
                    (accepted_count / total) * 100 if total > 0 else 0
                )

                # Update patterns
                self._update_patterns(command)
                break

        self._save_history()

    def track_execution_result(
        self, tracking_id: str, success: bool, output: str = None
    ):
        """
        Track the execution result of a command

        Args:
            tracking_id: The tracking ID of the suggestion
            success: Whether the command executed successfully
            output: The command output (optional)
        """
        for command in self.history["commands"]:
            if command["tracking_id"] == tracking_id:
                command["execution_success"] = success
                command["execution_output"] = (
                    output[:1000] if output else None
                )  # Limit output size
                command["execution_timestamp"] = datetime.now().isoformat()
                break

        self._save_history()

    def _update_patterns(self, command_entry: Dict):
        """
        Update pattern analysis based on user decision

        Args:
            command_entry: The command entry with user decision
        """
        if "patterns" not in self.history:
            self.history["patterns"] = {}

        patterns = self.history["patterns"]

        # Track patterns by command type
        cmd_type = command_entry["features"]["command_type"]
        if cmd_type not in patterns:
            patterns[cmd_type] = {"accepted": 0, "rejected": 0, "total": 0}

        patterns[cmd_type]["total"] += 1
        if command_entry["accepted"]:
            patterns[cmd_type]["accepted"] += 1
        else:
            patterns[cmd_type]["rejected"] += 1

        # Track patterns by request characteristics
        request_words = len(command_entry["user_request"].split())
        word_range = (
            "short"
            if request_words <= 3
            else "medium" if request_words <= 6 else "long"
        )

        if word_range not in patterns:
            patterns[word_range] = {"accepted": 0, "rejected": 0, "total": 0}

        patterns[word_range]["total"] += 1
        if command_entry["accepted"]:
            patterns[word_range]["accepted"] += 1
        else:
            patterns[word_range]["rejected"] += 1

    def get_suggestion_improvements(
        self, user_request: str, current_command: str
    ) -> Dict:
        """
        Get suggestions for improving command suggestions based on historical data

        Args:
            user_request: The current user request
            current_command: The currently suggested command

        Returns:
            Dictionary with improvement suggestions
        """
        improvements = {
            "confidence_score": 0.5,  # Default confidence
            "similar_accepted_commands": [],
            "pattern_insights": [],
            "recommendations": [],
        }

        if len(self.history["commands"]) < 5:
            improvements["recommendations"].append(
                "Insufficient data for pattern analysis"
            )
            return improvements

        # Analyze similar requests
        current_features = self._extract_command_features(
            current_command, user_request
        )
        similar_commands = self._find_similar_commands(
            user_request, current_features
        )

        if similar_commands:
            accepted_similar = [
                cmd for cmd in similar_commands if cmd["accepted"]
            ]
            improvements["similar_accepted_commands"] = [
                {
                    "command": cmd["suggested_command"],
                    "request": cmd["user_request"],
                    "success_rate": 1.0 if cmd["execution_success"] else 0.0,
                }
                for cmd in accepted_similar[:3]
            ]

        # Calculate confidence based on patterns
        cmd_type = current_features["command_type"]
        if cmd_type in self.history.get("patterns", {}):
            pattern = self.history["patterns"][cmd_type]
            if pattern["total"] > 0:
                acceptance_rate = pattern["accepted"] / pattern["total"]
                improvements["confidence_score"] = acceptance_rate

                if acceptance_rate < 0.3:
                    improvements["recommendations"].append(
                        f"Low acceptance rate for '{cmd_type}' commands"
                    )
                elif acceptance_rate > 0.8:
                    improvements["recommendations"].append(
                        f"High confidence - '{cmd_type}' commands usually accepted"
                    )

        # Analyze request length patterns
        request_words = len(user_request.split())
        word_range = (
            "short"
            if request_words <= 3
            else "medium" if request_words <= 6 else "long"
        )

        if word_range in self.history.get("patterns", {}):
            pattern = self.history["patterns"][word_range]
            if pattern["total"] > 0:
                acceptance_rate = pattern["accepted"] / pattern["total"]
                improvements["pattern_insights"].append(
                    f"{word_range.title()} requests have {acceptance_rate:.1%} acceptance rate"
                )

        return improvements

    def _find_similar_commands(
        self, user_request: str, features: Dict, limit: int = 5
    ) -> List[Dict]:
        """
        Find similar commands based on request and features

        Args:
            user_request: The current user request
            features: Features of the current command
            limit: Maximum number of similar commands to return

        Returns:
            List of similar command entries
        """
        similar = []
        request_words = set(user_request.lower().split())

        for cmd in self.history["commands"]:
            if cmd["accepted"] is None:  # Skip unresolved commands
                continue

            # Calculate similarity score
            cmd_words = set(cmd["user_request"].lower().split())
            word_overlap = len(request_words.intersection(cmd_words))
            word_similarity = word_overlap / max(
                len(request_words), len(cmd_words)
            )

            # Feature similarity
            feature_similarity = 0
            feature_count = 0
            for key, value in features.items():
                if key in cmd["features"]:
                    if isinstance(value, bool) and isinstance(
                        cmd["features"][key], bool
                    ):
                        if value == cmd["features"][key]:
                            feature_similarity += 1
                        feature_count += 1
                    elif isinstance(value, (int, float)) and isinstance(
                        cmd["features"][key], (int, float)
                    ):
                        # Normalize numeric features
                        max_val = max(abs(value), abs(cmd["features"][key]), 1)
                        similarity = (
                            1 - abs(value - cmd["features"][key]) / max_val
                        )
                        feature_similarity += similarity
                        feature_count += 1

            if feature_count > 0:
                feature_similarity /= feature_count

            # Combined similarity score
            total_similarity = (word_similarity * 0.6) + (
                feature_similarity * 0.4
            )

            if total_similarity > 0.3:  # Threshold for similarity
                similar.append({**cmd, "similarity_score": total_similarity})

        # Sort by similarity and return top results
        similar.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar[:limit]

    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about command tracking

        Returns:
            Dictionary with various statistics
        """
        stats = self.history["statistics"].copy()

        if len(self.history["commands"]) == 0:
            return stats

        # Recent activity (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_commands = [
            cmd
            for cmd in self.history["commands"]
            if datetime.fromisoformat(cmd["timestamp"]) > recent_cutoff
        ]

        stats["recent_activity"] = {
            "total_suggestions": len(recent_commands),
            "accepted": len(
                [cmd for cmd in recent_commands if cmd["accepted"] is True]
            ),
            "rejected": len(
                [cmd for cmd in recent_commands if cmd["accepted"] is False]
            ),
        }

        # Most common command types
        command_types = Counter()
        for cmd in self.history["commands"]:
            if cmd["features"]["command_type"]:
                command_types[cmd["features"]["command_type"]] += 1

        stats["top_command_types"] = dict(command_types.most_common(5))

        # Success rates by command type
        success_rates = {}
        for cmd_type in command_types.keys():
            type_commands = [
                cmd
                for cmd in self.history["commands"]
                if cmd["features"]["command_type"] == cmd_type
                and cmd["accepted"] is not None
            ]
            if type_commands:
                accepted = len(
                    [cmd for cmd in type_commands if cmd["accepted"]]
                )
                success_rates[cmd_type] = (accepted / len(type_commands)) * 100

        stats["success_rates_by_type"] = success_rates

        return stats

    def get_insights(self) -> List[str]:
        """
        Get actionable insights based on command tracking data

        Returns:
            List of insight strings
        """
        insights = []

        if len(self.history["commands"]) < 10:
            insights.append(
                "📊 Collecting data... More interactions needed for detailed insights"
            )
            return insights

        stats = self.get_statistics()

        # Overall acceptance rate insights
        acceptance_rate = stats["acceptance_rate"]
        if acceptance_rate > 80:
            insights.append(
                f"🎯 Excellent! {acceptance_rate:.1f}% command acceptance rate"
            )
        elif acceptance_rate > 60:
            insights.append(
                f"👍 Good {acceptance_rate:.1f}% command acceptance rate"
            )
        elif acceptance_rate > 40:
            insights.append(
                f"📈 Moderate {acceptance_rate:.1f}% acceptance rate - room for improvement"
            )
        else:
            insights.append(
                f"⚠️ Low {acceptance_rate:.1f}% acceptance rate - suggestions need improvement"
            )

        # Command type insights
        if "success_rates_by_type" in stats:
            best_type = max(
                stats["success_rates_by_type"].items(), key=lambda x: x[1]
            )
            worst_type = min(
                stats["success_rates_by_type"].items(), key=lambda x: x[1]
            )

            if best_type[1] > 80:
                insights.append(
                    f"✅ '{best_type[0]}' commands work well ({best_type[1]:.1f}% success)"
                )

            if worst_type[1] < 40:
                insights.append(
                    f"❌ '{worst_type[0]}' commands need improvement ({worst_type[1]:.1f}% success)"
                )

        # Recent activity insights
        if "recent_activity" in stats:
            recent = stats["recent_activity"]
            if recent["total_suggestions"] > 0:
                recent_rate = (
                    recent["accepted"] / recent["total_suggestions"]
                ) * 100
                if recent_rate > acceptance_rate + 10:
                    insights.append("📈 Recent suggestions are improving!")
                elif recent_rate < acceptance_rate - 10:
                    insights.append(
                        "📉 Recent suggestions declining - may need model adjustment"
                    )

        return insights

    def export_data(self, filepath: str = None) -> str:
        """
        Export command tracking data to a file

        Args:
            filepath: Optional custom filepath for export

        Returns:
            Path to the exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"command_tracking_export_{timestamp}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "insights": self.get_insights(),
            "command_history": self.history["commands"],
            "patterns": self.history.get("patterns", {}),
            "total_commands": len(self.history["commands"]),
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return filepath
        except IOError as e:
            raise IOError(f"Failed to export data: {e}")

    def clear_old_data(self, days_to_keep: int = 30):
        """
        Clear old command data to prevent the history file from growing too large

        Args:
            days_to_keep: Number of days of data to retain
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        original_count = len(self.history["commands"])
        self.history["commands"] = [
            cmd
            for cmd in self.history["commands"]
            if datetime.fromisoformat(cmd["timestamp"]) > cutoff_date
        ]

        removed_count = original_count - len(self.history["commands"])

        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old command entries")
            self._save_history()

        return removed_count
