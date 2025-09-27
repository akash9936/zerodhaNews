# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Setup and Installation
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
# Create .env file with:
# GROQ_API_KEY=your_groq_api_key_here
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# TELEGRAM_CHAT_ID=your_telegram_chat_id
```

### Running the Application
```bash
# Run news scraper to collect latest financial news
python scraper.py

# Run analyzer to generate AI-powered insights
python zerodha_news_analyzer.py

# Alternative analyzers (different AI models)
python groq.py
python deepseek.py
python CrewAI.py
```

### No Test Framework
This repository does not include automated tests. Testing is done manually by running the scrapers and analyzers.

## Architecture Overview

### Core Components

**News Collection Pipeline:**
- `scraper.py`: Selenium-based scraper for Zerodha Pulse news with configurable date/time ranges
- `zerodha_news_analyzer.py`: Main analyzer using Safari WebDriver for scraping + Groq API for analysis
- Data stored in `data/` directory as timestamped JSON files

**AI Analysis Engine:**
- Multiple analyzer implementations using different LLM providers:
  - `groq.py`: Groq API with Llama models (primary, cost-optimized)
  - `deepseek.py`: DeepSeek API integration
  - `CrewAI.py`: CrewAI framework implementation
- Batch processing to optimize API costs (15 items per batch)
- Structured output format with financial categories

**Output and Distribution:**
- `telegram_bot.py`: Telegram integration for automated report distribution
- Generates structured reports with sectors, opportunities, and macro implications
- GitHub Actions automation for scheduled runs (9 AM and 10 PM IST)

### Data Flow
1. Scraper collects news from Zerodha Pulse into JSON files
2. Analyzer processes news in batches through LLM APIs
3. Structured insights generated and saved as text reports
4. Telegram bot distributes reports to configured channels
5. GitHub Actions creates releases with report artifacts

### Key Configuration
- **Batch size**: 15 items per API call (cost optimization)
- **Token limits**: 800 max output tokens per call
- **Time filtering**: Configurable start date/time in `scraper.py`
- **Scheduling**: Automated runs via GitHub Actions cron jobs

### Environment Requirements
- Python 3.8+
- Selenium WebDriver (Chrome/Safari support)
- API keys for Groq, Telegram Bot
- Internet connection for web scraping and API calls

### Cost Optimization Features
- Batch processing reduces API calls by ~90%
- Uses cost-effective Groq Llama models (~$0.001 per run)
- Rate limiting and error handling
- Token counting and usage tracking