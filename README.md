# Zerodha News Scraper & Analyzer 📈

A powerful financial news analysis tool that scrapes news from various sources, processes them using AI, and generates structured trading insights and reports.

## 🌟 Features

- **Automated News Collection**: Scrapes financial news from multiple sources
- **AI-Powered Analysis**: Uses Groq's LLM to analyze news and generate insights
- **Structured Reports**: Creates well-organized reports with:
  - Key Sector Trends
  - Buy/Sell Opportunities
  - Macro Implications
  - Corporate Actions
- **Cost-Effective**: Optimized for minimal API usage while maintaining quality
- **Batch Processing**: Efficiently processes news in batches to reduce API calls

## 🛠️ Prerequisites

- Python 3.8 or higher
- Groq API key (get it from [Groq Console](https://console.groq.com/keys))
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

4. Create a `.env` file in the project root and add your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
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

1. Run the news scraper to collect latest news:
```bash
python scraper.py
```

2. Run the analyzer to generate insights:
```bash
python huggingface.py
```

The script will:
1. Load the latest news data
2. Process news in batches
3. Generate structured insights
4. Save a detailed report

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

Key parameters in `huggingface.py`:
- `batch_size`: Number of news items processed per API call (default: 15)
- `max_output_tokens`: Maximum tokens in AI response (default: 800)
- `temperature`: AI response creativity (default: 0.3)
- `top_p`: Response diversity (default: 0.8)

## 📈 Performance Metrics

The script tracks:
- Total news items processed
- API calls made
- Input/Output tokens used
- Processing time
- Sector distribution

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for informational purposes only. The generated insights should not be considered as financial advice. Always do your own research before making investment decisions.

## 🔗 Links

- [Groq API Documentation](https://console.groq.com/docs)
- [Python Documentation](https://docs.python.org/3/)
- [Project Issues](https://github.com/yourusername/ZerodhaNewsScrapper/issues) 