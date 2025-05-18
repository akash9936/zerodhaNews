import json
import os
import sys
import time
import requests
from dotenv import load_dotenv

def get_api_key():
    """Get Hugging Face API key with validation."""
    load_dotenv()
    api_key = os.getenv("HUGGINGFACE_API_KEY")

    while not api_key or not api_key.startswith("hf_"):
        print("Hugging Face API key not found or invalid.")
        print("Get a free key from: https://huggingface.co/settings/tokens")
        api_key = input("Enter your API key (starts with 'hf_'): ").strip()
    
    return api_key

def analyze_news(api_key, news_data):
    """Analyze news using Hugging Face's Mixtral model."""
    system_prompt = """You are an expert stock market analyst. Analyze these news articles and generate:
1. **Key Sector Trends** 🌍📈  
2. **Buy/Sell Opportunities** 💰🔍 (with rationale)  
3. **Macro Implications** 🏦📉  
4. **Corporate Actions** 🗓️🏢  

Use Markdown with clear headings and emojis. Be concise."""

    user_prompt = "NEWS DATA:\n" + json.dumps(news_data, indent=2)
    url = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "inputs": f"<s>[INST] {system_prompt}\n\n{user_prompt} [/INST]",
        "parameters": {
            "temperature": 0.3,
            "max_new_tokens": 1500,
            "return_full_text": False,
        }
    }

    for _ in range(3):  # Retry 3 times
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 503:  # Model loading
                time.sleep(15)
                continue
            response.raise_for_status()
            return response.json()[0]["generated_text"]
        except Exception as e:
            print(f"Retrying... Error: {e}")
            time.sleep(5)
    
    raise Exception("API request failed after retries.")

def main():
    try:
        api_key = get_api_key()
        
        # Load news data
        try:
            with open("pulse_news_20250519_010826.json", "r") as f:
                news_data = json.load(f)
        except Exception as e:
            print(f"Failed to load news data: {e}")
            sys.exit(1)

        print("Analyzing news...")
        analysis = analyze_news(api_key, news_data)
        
        with open("market_report.md", "w") as f:
            f.write(analysis)
        
        print(f"Report saved to: {os.path.abspath('market_report.md')}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()