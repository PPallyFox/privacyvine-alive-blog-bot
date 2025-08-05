import os
import random
import time
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import date
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ===== CONFIG =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RSS_FEED = "https://www.bleepingcomputer.com/feed/"
SERVICE_ACCOUNT_FILE = "service_account.json"  # Created by GitHub Actions
SPREADSHEET_ID = "1cf6_ckhsGATV1L-jybALBqItmLlABf0gURrA-f6sY4g"
RANGE_NAME = "LinkedIn_Content_Calendar_Template!A:E"



# ===== GOOGLE SHEETS SETUP =====
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
service = build('sheets', 'v4', credentials=credentials)
sheet = service.spreadsheets()

# ===== OPENAI CLIENT =====
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== FETCH FULL ARTICLE =====
def fetch_full_article(link):
    try:
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

        print(f"🔍 Fetching full article for: {link}")

        response = requests.get(link, headers=headers, timeout=10)
        if response.status_code == 403:
            print("⚠️ 403 Forbidden — retrying with different headers...")
            time.sleep(2)
            headers["User-Agent"] = random.choice(user_agents)
            response = requests.get(link, headers=headers, timeout=10)

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        article_body = soup.find("div", class_="articleBody") or soup.find("div", class_="articleBodyContent")

        if not article_body:
            print("⚠️ RSS FALLBACK — Could not find full article content.")
            return ""

        paragraphs = article_body.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)

        print("✅ FULL ARTICLE SCRAPED SUCCESSFULLY")
        print("\n===== SCRAPED ARTICLE PREVIEW =====")
        print(text[:500] + ("..." if len(text) > 500 else ""))
        print("===================================\n")
        return text

    except Exception as e:
        print(f"⚠️ RSS FALLBACK — Failed to fetch article: {e}")
        return ""

# ===== AI SUMMARY =====
def summarize_article(title, link, content):
    prompt = f"""
Summarize this cybersecurity news in a professional LinkedIn tone.

Title: {title}
Link: {link}
Content: {content}

Format:
- Headline
- 2-3 sentence summary
- Why it matters
- Security tip

End with: "Patrick used AI to automate this post."
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ===== WRITE TO GOOGLE SHEETS =====
def write_to_google_sheet(date_str, content, status, url):
    values = [[date_str, content, "Draft", status, url]]
    body = {'values': values}
    result = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    print(f"✅ {result.get('updates').get('updatedRows')} row(s) appended to Google Sheet.")

# ===== MAIN BOT =====
def run_bot():
    try:
        feed = feedparser.parse(RSS_FEED)
        if not feed.entries:
            print("⚠️ No entries found in RSS feed.")
            write_to_google_sheet(date.today().isoformat(), "No articles found", "Failed", "")
            return

        top_story = feed.entries[0]
        full_article = fetch_full_article(top_story.link)

        if full_article:
            summary = summarize_article(top_story.title, top_story.link, full_article)
        else:
            print("ℹ️ Using RSS description as fallback.")
            rss_description = getattr(top_story, "description", "")
            summary = summarize_article(top_story.title, top_story.link, rss_description)

        write_to_google_sheet(date.today().isoformat(), summary, "Success", top_story.link)
        print(f"✅ LinkedIn post added for: {top_story.title}")

    except Exception as e:
        print(f"❌ Bot failed: {e}")
        write_to_google_sheet(date.today().isoformat(), f"Error: {e}", "Failed", "")

if __name__ == "__main__":
    run_bot()
