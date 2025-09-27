#!/usr/bin/env python3
"""
Test runner script for the Zerodha News Analyzer
"""
import sys
import subprocess
import os


def run_unit_tests():
    """Run unit tests"""
    print("🧪 Running unit tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_time_utils.py",
        "tests/test_text_utils.py",
        "tests/test_api_utils.py",
        "tests/test_news_scraper.py",
        "tests/test_news_analyzer.py",
        "tests/test_report_generator.py",
        "tests/test_notification_service.py",
        "-v", "--tb=short"
    ], capture_output=False)
    return result.returncode


def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running integration tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/test_pipeline_orchestrator.py",
        "-v", "--tb=short"
    ], capture_output=False)
    return result.returncode


def run_all_tests():
    """Run all tests"""
    print("🚀 Running all tests...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v", "--tb=short"
    ], capture_output=False)
    return result.returncode


def run_coverage():
    """Run tests with coverage"""
    print("📊 Running tests with coverage...")
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-exclude=tests/*",
        "-v"
    ], capture_output=False)

    if result.returncode == 0:
        print("\n📋 Coverage report generated in htmlcov/index.html")

    return result.returncode


def check_requirements():
    """Check if test requirements are installed"""
    try:
        import pytest
        import pytest_cov
        print("✅ Test dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing test dependencies: {e}")
        print("💡 Install with: pip install -r requirements-test.txt")
        return False


def main():
    """Main test runner"""
    if not check_requirements():
        return 1

    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()

        if test_type == "unit":
            return run_unit_tests()
        elif test_type == "integration":
            return run_integration_tests()
        elif test_type == "coverage":
            return run_coverage()
        elif test_type == "all":
            return run_all_tests()
        else:
            print(f"❌ Unknown test type: {test_type}")
            print("💡 Available options: unit, integration, coverage, all")
            return 1
    else:
        return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())