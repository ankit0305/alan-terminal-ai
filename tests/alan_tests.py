#!/usr/bin/env python3
"""
Real-time tests for Alan Terminal Assistant (no mocks)
Tests show_help and execute_command with actual system calls
"""

import os
import sys
from io import StringIO

from alan_assistant import AlanAssistant

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")))


class TestShowHelpReal:
    """Real tests for show_help functionality"""

    def test_show_help_produces_output(self):
        """Test that show_help actually prints help text"""
        alan = AlanAssistant()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            alan.show_help()
            help_text = captured_output.getvalue()

            assert len(help_text.strip()) > 0, "Help text should not be empty"
            assert "alan" in help_text.lower(), "Help should mention 'alan'"
            assert (
                "usage" in help_text.lower() or "please" in help_text.lower()
            ), "Help should show usage"

        finally:
            sys.stdout = old_stdout

    def test_show_help_multiline_output(self):
        """Test that help produces multiple lines of output"""
        alan = AlanAssistant()

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            alan.show_help()
            help_text = captured_output.getvalue()

            lines = help_text.strip().split("\n")
            assert len(
                lines) >= 3, "Help should have multiple lines of information"

        finally:
            sys.stdout = old_stdout


class TestExecuteCommandReal:
    """Real tests for execute_command functionality - actually runs commands"""

    def test_execute_ls_command(self):
        """Test executing 'ls' command on Mac (like 'alan please list files')"""
        alan = AlanAssistant()

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            success = alan.execute_command("ls")
            captured_output.getvalue()
            assert success is not False, "ls command should execute successfully"

        finally:
            sys.stdout = old_stdout


# Simple test runner
def run_real_tests():
    """Run all tests and report results"""
    print("🧪 Running Real-Time Tests for Alan Terminal Assistant")
    print("=" * 60)

    test_classes = [TestShowHelpReal, TestExecuteCommandReal]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n📋 Running {test_class.__name__}:")

        test_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]

        for test_method in test_methods:
            total_tests += 1
            test_name = test_method.replace(
                "test_", "").replace("_", " ").title()

            try:
                test_instance = test_class()
                getattr(test_instance, test_method)()

                print(f"  ✅ {test_name}")
                passed_tests += 1

            except Exception as e:
                print(f"  ❌ {test_name}: {str(e)}")
                failed_tests.append(
                    f"{test_class.__name__}.{test_method}: {str(e)}")

    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("\n❌ Failed Tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return 1

    print("\n🎉 All tests passed!")
    return 0


if __name__ == "__main__":
    EXIT_CODE = run_real_tests()
    sys.exit(EXIT_CODE)
