#!/usr/bin/env python3
"""
Test script for command tracking functionality
"""

import os
import sys

from alan_assistant import AlanAssistant
from command_tracker import CommandTracker


def test_command_tracker():
    """Test the command tracker functionality"""
    print("🧪 Testing Command Tracking System")
    print("=" * 50)

    # Create a test tracker with a temporary file
    test_file = "test_command_history.json"
    tracker = CommandTracker(test_file)

    # Test 1: Track a command suggestion
    print("Test 1: Tracking command suggestion...")
    tracking_id = tracker.track_suggestion(
        user_request="list files",
        suggested_command="ls -la",
        model_used="test_model",
        system_info={"name": "macOS", "type": "unix"},
    )
    print(f"✅ Tracked suggestion with ID: {tracking_id}")

    # Test 2: Track user decision (acceptance)
    print("\nTest 2: Tracking user acceptance...")
    tracker.track_user_decision(tracking_id, accepted=True)
    print("✅ Tracked user acceptance")

    # Test 3: Track execution result
    print("\nTest 3: Tracking execution result...")
    tracker.track_execution_result(
        tracking_id, success=True, output="file1.txt\nfile2.txt"
    )
    print("✅ Tracked execution result")

    # Test 4: Get statistics
    print("\nTest 4: Getting statistics...")
    stats = tracker.get_statistics()
    print(f"✅ Total suggestions: {stats['total_suggestions']}")
    print(f"✅ Acceptance rate: {stats['acceptance_rate']:.1f}%")

    # Test 5: Get insights
    print("\nTest 5: Getting insights...")
    insights = tracker.get_insights()
    for insight in insights:
        print(f"💡 {insight}")

    # Test 6: Test suggestion improvements
    print("\nTest 6: Testing suggestion improvements...")
    improvements = tracker.get_suggestion_improvements("show files", "ls -l")
    print(f"✅ Confidence score: {improvements['confidence_score']:.2f}")
    print(f"✅ Recommendations: {len(improvements['recommendations'])}")

    # Test 7: Add more test data
    print("\nTest 7: Adding more test data...")
    test_commands = [
        ("show disk usage", "df -h", True, True),
        ("find python files", "find . -name '*.py'", True, True),
        ("check processes", "ps aux", False, None),
        ("show current directory", "pwd", True, True),
        ("list hidden files", "ls -la", True, True),
    ]

    for request, command, accepted, success in test_commands:
        tid = tracker.track_suggestion(
            request, command, "test_model", {"name": "macOS", "type": "unix"}
        )
        tracker.track_user_decision(tid, accepted)
        if success is not None:
            tracker.track_execution_result(tid, success)

    print(f"✅ Added {len(test_commands)} more test commands")

    # Test 8: Final statistics
    print("\nTest 8: Final statistics...")
    final_stats = tracker.get_statistics()
    print(f"✅ Total suggestions: {final_stats['total_suggestions']}")
    print(f"✅ Accepted: {final_stats['total_accepted']}")
    print(f"✅ Rejected: {final_stats['total_rejected']}")
    print(f"✅ Acceptance rate: {final_stats['acceptance_rate']:.1f}%")

    if "top_command_types" in final_stats:
        print("✅ Top command types:")
        for cmd_type, count in final_stats["top_command_types"].items():
            print(f"   • {cmd_type}: {count}")

    # Test 9: Export data
    print("\nTest 9: Testing data export...")
    export_file = tracker.export_data("test_export.json")
    print(f"✅ Exported data to: {export_file}")

    # Cleanup
    print("\nCleaning up test files...")
    for file in [test_file, export_file]:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  Removed {file}")

    print("\n🎉 All tests passed!")


def test_alan_integration():
    """Test the integration with AlanAssistant"""
    print("\n🧪 Testing Alan Assistant Integration")
    print("=" * 50)

    alan = AlanAssistant()

    # Test tracking methods
    print("Test 1: Testing command suggestion tracking...")
    tracking_id = alan.track_command_suggestion(
        "test request", "echo 'test'", "test_model"
    )
    print(f"✅ Tracking ID: {tracking_id}")

    print("\nTest 2: Testing user decision tracking...")
    alan.track_user_decision(True, "Test feedback")
    print("✅ User decision tracked")

    print("\nTest 3: Testing execution result tracking...")
    alan.track_execution_result(True, "test output")
    print("✅ Execution result tracked")

    print("\nTest 4: Testing insights...")
    insights = alan.get_command_insights("test request", "echo 'test'")
    print(f"✅ Got insights: {len(insights)} categories")

    print("\n🎉 Integration tests passed!")


if __name__ == "__main__":
    try:
        test_command_tracker()
        test_alan_integration()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
