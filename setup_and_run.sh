#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}==== Zerodha News Analyzer Setup ====${NC}"

# Check if Python 3.8+ is installed
python_version=$(python3 -c 'import sys; v = sys.version_info; print(f"{v.major}.{v.minor}")')
required_version="3.8"

# Compare versions using sort -V (natural version sort)
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python 3.8 or higher is required. Current version: $python_version${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade pip and setuptools
echo -e "${YELLOW}Upgrading pip and setuptools...${NC}"
python3 -m pip install --upgrade pip setuptools wheel

# Install required packages with error handling
echo -e "${YELLOW}Installing required packages...${NC}"
if ! pip install -r requirements.txt; then
    echo -e "${RED}Error: Failed to install required packages.${NC}"
    echo -e "${YELLOW}Attempting to install packages one by one...${NC}"
    
    # Try installing packages one by one
    while IFS= read -r package || [ -n "$package" ]; do
        # Skip comments and empty lines
        [[ $package =~ ^#.*$ || -z $package ]] && continue
        echo -e "${YELLOW}Installing $package...${NC}"
        if ! pip install "$package"; then
            echo -e "${RED}Failed to install $package${NC}"
            exit 1
        fi
    done < requirements.txt
fi

# Create data directory if it doesn't exist
mkdir -p data

# Check Safari setup
echo -e "${YELLOW}Checking Safari setup...${NC}"
echo -e "Please ensure you have:"
echo -e "1. Enabled the Develop menu in Safari (Safari > Settings > Advanced > Show Develop menu)"
echo -e "2. Enabled Remote Automation (Develop > Allow Remote Automation)"
echo -e "3. Trusted the WebDriver in System Preferences > Security & Privacy"
echo -e "\nPress Enter to continue or Ctrl+C to exit..."
read

# Check for Groq API key
if [ ! -f ".env" ] || ! grep -q "GROQ_API_KEY" .env; then
    echo -e "${YELLOW}Groq API key not found.${NC}"
    echo -e "Please enter your Groq API key (starts with 'gsk_'):"
    read -r api_key
    echo "GROQ_API_KEY=$api_key" > .env
    echo -e "${GREEN}API key saved to .env file${NC}"
fi

# Verify critical packages are installed
echo -e "${YELLOW}Verifying critical packages...${NC}"
if ! python3 -c "import requests, selenium, dotenv" 2>/dev/null; then
    echo -e "${RED}Error: Critical packages are not installed correctly.${NC}"
    exit 1
fi

# Run the script
echo -e "${GREEN}Setup complete! Running the news analyzer...${NC}"
python3 zerodha_news_analyzer.py

# Deactivate virtual environment
deactivate

echo -e "${GREEN}Done!${NC}"