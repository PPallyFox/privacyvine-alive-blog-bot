import feedparser
import os
import csv
from datetime import date
from openai import OpenAI

# ===== CONFIG =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RSS_FEED = "https://www.bleepingcomputer.com/feed/"
CSV_FILE = "linkedin_posts.csv"

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== AI SUMMARY =====
def summarize_article(title, link, description):
    prompt = f"""
    Summarize this cybersecurity news in a professional LinkedIn tone.
    Title: {title}
    Link: {link}
    Description: {description}

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
    # Check if CSV exists
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
    summary = summarize_article(
        top_story.title, 
        top_story.link, 
        getattr(top_story, "description", "")
    )
    
    write_csv(summary)
    print(f"✅ LinkedIn post added for: {top_story.title}")

if __name__ == "__main__":
    run_bot()
