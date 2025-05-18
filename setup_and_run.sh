#!/bin/bash

# This script helps you set up and run the Zerodha Pulse scraper on macOS

echo "==== Zerodha Pulse Scraper Setup ===="

# Create and activate a virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install selenium webdriver-manager

# Download ChromeDriver using webdriver-manager
echo "Downloading ChromeDriver..."
python3 -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"

# Get the path to the installed ChromeDriver
DRIVER_PATH=$(python3 -c "from webdriver_manager.chrome import ChromeDriverManager; print(ChromeDriverManager().install())")

# Remove quarantine attribute
echo "Removing quarantine attribute from ChromeDriver..."
xattr -d com.apple.quarantine "$DRIVER_PATH" 2>/dev/null || sudo xattr -d com.apple.quarantine "$DRIVER_PATH"

echo "Setup complete! Now running the scraper..."
python3 scraper.py

echo "Done!"