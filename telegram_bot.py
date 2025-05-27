import os
import requests
from typing import List, Dict
import json
import re

class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def escape_markdown(self, text: str) -> str:
        """Escape special characters for Telegram Markdown."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def format_message(self, section_name: str, content: str) -> str:
        """Format the message with proper Markdown escaping."""
        # Escape special characters in content
        content = self.escape_markdown(content)
        
        # Format section name with bold and emoji
        formatted_name = f"*{self.escape_markdown(section_name)}* 🌟"
        
        # Clean up the content
        # Remove multiple newlines
        content = re.sub(r'\n\s*\n', '\n\n', content)
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return f"{formatted_name}\n\n{content}"

    def send_message(self, text: str, parse_mode: str = "MarkdownV2") -> bool:
        """Send a message to the specified chat.
        
        Args:
            text (str): The message text to send
            parse_mode (str): The parse mode to use ("MarkdownV2" or "HTML")
        """
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response content: {e.response.text}")
            return False

def parse_news_report(file_path: str) -> Dict[str, str]:
    """Parse the news report file and extract different sections."""
    sections = {
        "Key Sector Trends": "",
        "Buy Opportunities": "",
        "Macro Implications": "",
        "Earnings Results": "",
        "Dividend Announcements": "",
        "Business Updates": ""
    }
    
    current_section = None
    section_content = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            
            # Skip empty lines and decorative lines
            if not line or line.startswith('╔') or line.startswith('║') or line.startswith('╚'):
                continue
                
            # Check for section headers
            if line.startswith('* **Key Sector Trends**'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                current_section = "Key Sector Trends"
                section_content = [line.replace('* **', '').replace('**', '')]  # Clean up markdown
            elif line.startswith('* **Buy**'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                current_section = "Buy Opportunities"
                section_content = [line.replace('* **', '').replace('**', '')]  # Clean up markdown
            elif line.startswith('* **Macro Implications**'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                current_section = "Macro Implications"
                section_content = [line.replace('* **', '').replace('**', '')]  # Clean up markdown
            elif line.startswith('* **Earnings Results**'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                current_section = "Earnings Results"
                section_content = [line.replace('* **', '').replace('**', '')]  # Clean up markdown
            elif line.startswith('* **Dividend Announcements**'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                current_section = "Dividend Announcements"
                section_content = [line.replace('* **', '').replace('**', '')]  # Clean up markdown
            elif line.startswith('* **Business Updates**'):
                if current_section and section_content:
                    sections[current_section] = '\n'.join(section_content)
                current_section = "Business Updates"
                section_content = [line.replace('* **', '').replace('**', '')]  # Clean up markdown
            elif current_section:
                # Clean up bullet points and other markdown
                line = line.replace('* ', '• ').replace('+ ', '• ')
                section_content.append(line)
    
    # Add the last section
    if current_section and section_content:
        sections[current_section] = '\n'.join(section_content)
    
    return sections

def main():
    # Get Telegram bot token and chat ID from environment variables
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Error: Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return
    
    # Initialize Telegram bot
    bot = TelegramBot(token, chat_id)
    
    # Get the latest news report file
    news_files = [f for f in os.listdir('data') if f.startswith('zerodha_news_report_') and f.endswith('.txt')]
    if not news_files:
        print("No news report files found in data directory")
        return
    
    latest_file = sorted(news_files)[-1]
    file_path = os.path.join('data', latest_file)
    
    # Parse the news report
    sections = parse_news_report(file_path)
    
    # Send each section as a separate message
    for section_name, content in sections.items():
        if content:  # Only send non-empty sections
            try:
                message = bot.format_message(section_name, content)
                if bot.send_message(message):
                    print(f"Successfully sent {section_name} section")
                else:
                    print(f"Failed to send {section_name} section")
            except Exception as e:
                print(f"Error formatting/sending {section_name} section: {e}")

if __name__ == "__main__":
    main() 