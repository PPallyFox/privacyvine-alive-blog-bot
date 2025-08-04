import random
import time
import requests
from bs4 import BeautifulSoup

def fetch_full_article(link):
    try:
        # Rotate between a few browser-like user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0"
        ]

        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }

        # First request
        response = requests.get(link, headers=headers, timeout=10)
        if response.status_code == 403:
            print("⚠️ 403 Forbidden — retrying with different headers...")
            time.sleep(2)  # Short pause to look less bot-like
            headers["User-Agent"] = random.choice(user_agents)
            response = requests.get(link, headers=headers, timeout=10)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # BleepingComputer article container
        article_body = soup.find("div", class_="articleBody") or soup.find("div", class_="articleBodyContent")
        if not article_body:
            return ""  # Fallback if structure changes
        
        paragraphs = article_body.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)

        # Show preview in Actions log
        print("\n===== SCRAPED ARTICLE PREVIEW =====")
        print(text[:500] + ("..." if len(text) > 500 else ""))
        print("===================================\n")
        return text

    except Exception as e:
        print(f"⚠️ Failed to fetch article: {e}")
        return ""
