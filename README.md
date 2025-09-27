# Zerodha News Scraper & Analyzer 📈

A powerful, modular financial news analysis tool that scrapes news from Zerodha Pulse, processes them using AI, and generates structured trading insights with automated Telegram notifications.

## 🌟 Features

- **Automated News Collection**: Scrapes financial news from Zerodha Pulse
- **AI-Powered Analysis**: Uses Groq's LLM to analyze news and generate insights
- **Modular Architecture**: Clean, maintainable code with separated concerns
- **Structured Reports**: Creates well-organized reports with:
  - Key Sector Trends 🌍📈
  - Buy/Sell Opportunities 💰🔍
  - Macro Implications 🏦📉
  - Corporate Actions 🗓️🏢
- **Telegram Integration**: Automatic report delivery via Telegram bot
- **Cost-Effective**: Optimized for minimal API usage (~$0.001 per run)
- **Batch Processing**: Efficiently processes news in batches to reduce API calls
- **Comprehensive Testing**: 130+ test cases with full coverage
- **Error Handling**: Robust error management with comprehensive logging

## 🛠️ Prerequisites

- Python 3.8 or higher
- Groq API key (get it from [Groq Console](https://console.groq.com/keys))
- Telegram Bot Token (optional, for notifications)
- Required Python packages (see Installation section)

## 📥 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ZerodhaNewsScrapper.git
cd ZerodhaNewsScrapper
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token (optional)
TELEGRAM_CHAT_ID=your_telegram_chat_id (optional)
```

## 💰 Cost Analysis

The script is optimized for cost efficiency:
- Uses Groq's "meta-llama/llama-4-scout-17b-16e-instruct" model
- Average cost per run: ~$0.00114 (0.11 cents)
- Free tier includes $10 in credits (enough for ~8,770 runs)
- Cost optimization features:
  - Batch processing (15 items per batch)
  - Limited output tokens (800 per call)
  - Concise prompts
  - Rate limiting

## 🚀 Usage

### Quick Start (Recommended)
Run the complete pipeline with one command:
```bash
python3 pipeline_orchestrator.py
```

### Alternative Methods

#### Using the original entry point:
```bash
python3 zerodha_news_analyzer.py
```

#### Using individual components:
```bash
# 1. Scrape news only
python -c "from news_scraper import ZerodhaPulseScraper; scraper = ZerodhaPulseScraper(); scraper.scrape_news()"

# 2. Run analysis on existing data
python -c "from pipeline_orchestrator import NewsAnalysisPipeline; pipeline = NewsAnalysisPipeline(); pipeline.run_complete_pipeline()"
```

#### Using Make commands:
```bash
# Run the pipeline
make run

# Run using legacy method
make run-legacy

# Run demo (with confirmation)
make demo
```

The pipeline will:
1. 🔍 Scrape latest news from Zerodha Pulse
2. 🤖 Analyze using AI (Groq API)
3. 📊 Generate structured report
4. 💾 Save report to `data/` directory
5. 📱 Send formatted report to Telegram (if configured)


## 📊 Output Format

The generated report includes:
```
╔══════════════════════════════════════════════════════════════════╗
║                📈 STRUCTURED FINANCIAL NEWS REPORT 📈            ║
║                        [Timestamp]                               ║
╚══════════════════════════════════════════════════════════════════╝

📊 Analysis Summary
- Total news items analyzed
- Sector distribution
- API usage statistics

**Key Sector Trends** 🌍📈
- Sector-wise developments with specific company details

**Buy/Sell Opportunities** 💰🔍
- Specific stock recommendations with reasoning
- Technical breakouts and analyst calls

**Macro Implications** 🏦📉
- Economic and policy impacts
- Market sentiment indicators

**Corporate Actions** 🗓️🏢
- Earnings results
- Dividend announcements
- Business updates
```

## 🔧 Configuration

The application uses a modular configuration system. Key settings are in `config.py`:

### Analysis Configuration
- `BATCH_SIZE`: Number of news items processed per API call (default: 15)
- `MAX_TOKENS`: Maximum tokens in AI response (default: 800)
- `TEMPERATURE`: AI response creativity (default: 0.3)
- `TOP_P`: Response diversity (default: 0.8)

### File Configuration
- `DATA_DIR`: Directory for storing data files (default: 'data')
- `REPORT_FILENAME_FORMAT`: Template for report filenames
- `ENCODING`: File encoding (default: 'utf-8')

### Telegram Configuration
- `MAX_MESSAGE_LENGTH`: Maximum length per Telegram message (default: 4000)
- `PARSE_MODE`: Message formatting mode (default: 'HTML')

## 📈 Performance Metrics

The pipeline tracks and reports:
- Total news items processed
- API calls made and cost optimization
- Processing time and efficiency
- Sector distribution and categorization
- Success/failure rates for each component
- Notification delivery status

## 🧪 Testing

The project includes a comprehensive test suite with 130+ test cases covering all modules.

### Running Tests

#### Quick Start
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
make test

# Or using the test runner directly
python3 tests/test_runner.py
```

#### Specific Test Types
```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Tests with coverage report
make test-coverage

# Quick run without verbose output
make test-quick
```

#### Individual Modules
```bash
# Test specific module
pytest tests/test_news_scraper.py -v

# Test specific function
pytest tests/test_time_utils.py::TestTimeUtils::test_get_ist_time -v
```

### Test Structure
```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_time_utils.py            # Time utility functions (12 tests)
├── test_text_utils.py            # Text processing functions (15 tests)
├── test_api_utils.py             # API utility functions (10 tests)
├── test_news_scraper.py          # News scraping module (12 tests)
├── test_news_analyzer.py         # AI analysis module (18 tests)
├── test_report_generator.py      # Report generation (12 tests)
├── test_notification_service.py  # Notification service (14 tests)
├── test_pipeline_orchestrator.py # Integration tests (15 tests)
└── test_runner.py                # Custom test runner
```

### Coverage
The test suite provides comprehensive coverage including:
- ✅ Unit tests for all utility functions
- ✅ Integration tests for the complete pipeline
- ✅ Error handling and edge cases
- ✅ Mock testing for external dependencies
- ✅ Configuration and environment testing

## 🏗️ Architecture

The application follows a modular architecture with clear separation of concerns:

```
├── config.py                 # Centralized configuration
├── pipeline_orchestrator.py  # Main pipeline coordinator
├── news_scraper.py           # News collection from Zerodha Pulse
├── news_analyzer.py          # AI-powered analysis engine
├── report_generator.py       # Report formatting and saving
├── notification_service.py   # Telegram and other notifications
├── error_handler.py          # Centralized error management
├── utils/                    # Utility functions
│   ├── time_utils.py         # Time handling utilities
│   ├── text_utils.py         # Text processing functions
│   └── api_utils.py          # API credential management
└── zerodha_news_analyzer.py  # Legacy entry point (backward compatibility)
```

### Benefits of Modular Design:
- **Maintainability**: Easy to update individual components
- **Testability**: Each module can be tested independently
- **Extensibility**: Simple to add new features or data sources
- **Reusability**: Components can be used in other projects

## 🔄 GitHub Actions Integration

The project includes automated workflows for scheduled news analysis:
- Runs at 9 AM and 10 PM IST daily
- Automatically creates releases with generated reports
- Includes comprehensive error handling and notifications

## 🛠️ Development

### Setup Development Environment
```bash
# Install all dependencies (including test dependencies)
make setup-dev

# Or manually:
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Development Commands
```bash
# Run the pipeline
make run

# Run tests
make test

# Run linting (requires flake8)
make lint

# Format code (requires black)
make format

# Run all checks
make check

# Clean up generated files
make clean
```

### Adding New Features
1. **New Data Sources**: Extend `news_scraper.py` or create new scraper classes
2. **Analysis Models**: Modify `news_analyzer.py` to support different LLM providers
3. **Notification Channels**: Add new services to `notification_service.py`
4. **Report Formats**: Extend `report_generator.py` for different output formats

### Testing Guidelines
- Write tests for all new functionality
- Maintain test coverage above 90%
- Use proper mocking for external dependencies
- Follow the existing test structure and naming conventions

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Unit tests for additional edge cases
- Support for additional news sources
- Enhanced error recovery mechanisms
- Performance optimizations
- UI/Web interface
- Additional notification channels (Slack, Discord, etc.)

### Contributing Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

Please ensure your code follows the existing style and includes appropriate tests.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for informational purposes only. The generated insights should not be considered as financial advice. Always do your own research before making investment decisions.

## 🔗 Links

- [Groq API Documentation](https://console.groq.com/docs)
- [Python Documentation](https://docs.python.org/3/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Pytest Documentation](https://docs.pytest.org/)
- [Project Issues](https://github.com/yourusername/ZerodhaNewsScrapper/issues) 