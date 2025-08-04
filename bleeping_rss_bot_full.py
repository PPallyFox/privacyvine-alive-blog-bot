import feedparser
import os
import csv
import requests
from bs4 import BeautifulSoup
from datetime import date
from openai import OpenAI

# ===== CONFIG =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RSS_FEED = "https://www.bleepingcomputer.com/feed/"
CSV_FILE = "linkedin_posts.csv"

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== FETCH FULL ARTICLE =====
def fetch_full_article(link):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(link, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")

        # BleepingComputer articles are inside div.articleBody or div.articleBodyContent
        article_body = soup.find("div", class_="articleBody") or soup.find("div", class_="articleBodyContent")
        if not article_body:
            return ""
        
        paragraphs = article_body.find_all("p")
        text = "\n".join(p.get_text(strip=True) for p in paragraphs)
        return text

    except Exception as e:
        print(f"⚠️ Failed to fetch article: {e}")
        return ""

# ===== AI SUMMARY =====
def summarize_article(title, link, content):
    prompt = f"""
    Summarize this cybersecurity news in a professional LinkedIn tone.
    Title: {title}
    Link: {link}
    Article Content: {content}

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

# ===== WRITE TO CSV =====
def write_csv(content):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, mode="a", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Date", "Post Content"])
        writer.writerow([date.today().isoformat(), content])

# ===== MAIN BOT =====
def run_bot():
    feed = feedparser.parse(RSS_FEED)
    
    if not feed.entries:
        print("⚠️ No entries found in RSS feed.")
        return
    
    top_story = feed.entries[0]
    
    print(f"🔍 Fetching full article for: {top_story.title}")
    full_content = fetch_full_article(top_story.link)
    
    if not full_content:
        full_content = getattr(top_story, "description", "")
        print("⚠️ Using RSS description as fallback.")
    
    summary = summarize_article(
        top_story.title, 
        top_story.link, 
        full_content
    )

    # ===== PREVIEW OUTPUT IN ACTIONS LOG =====
    print("\n===== SCRAPED ARTICLE PREVIEW =====")
    print(full_content[:500] + "...\n")  # show first 500 chars
    print("===== GPT SUMMARY =====")
    print(summary)
    
    write_csv(summary)
    print(f"✅ LinkedIn post added for: {top_story.title}")

if __name__ == "__main__":
    run_bot()
