import feedparser
import requests
import openai
from datetime import date
import os

# ===== CONFIGURATION =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SQUARESPACE_API_KEY = os.getenv("SQUARESPACE_API_KEY")
SQUARESPACE_SITE_ID = os.getenv("SQUARESPACE_SITE_ID")

RSS_FEED = "https://www.bleepingcomputer.com/feed/"
MEMORY_FILE = "last_posted.txt"

# ===== AI SUMMARIZATION =====
def summarize_article(title, link, description):
    openai.api_key = OPENAI_API_KEY
    prompt = f"""
    Summarize this cybersecurity news story in a professional tone for the PrivacyVine Alive Blog.
    Title: {title}
    Link: {link}
    Description: {description}
    
    Provide:
    - A concise summary (2-3 sentences)
    - Why it matters
    - 1 security tip
    
    End with: 'Patrick used AI to automate this post.'
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message["content"]

# ===== PUBLISH TO SQUARESPACE =====
def publish_to_squarespace(title, body):
    url = f"https://api.squarespace.com/1.0/sites/{SQUARESPACE_SITE_ID}/blog-posts"
    headers = {
        "Authorization": f"Bearer {SQUARESPACE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "body": body,
        "publishOn": date.today().isoformat(),
        "state": "PUBLISHED"
    }
    r = requests.post(url, json=data, headers=headers)
    if r.status_code == 201:
        print(f"✅ Published: {title}")
    else:
        print(f"❌ Error: {r.status_code}, {r.text}")

# ===== MEMORY CHECK =====
def already_posted(link):
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            last_link = f.read().strip()
        return last_link == link
    return False

def save_posted(link):
    with open(MEMORY_FILE, "w") as f:
        f.write(link)

# ===== MAIN BOT FUNCTION =====
def run_bot():
    feed = feedparser.parse(RSS_FEED)
    top_story = feed.entries[0]

    if already_posted(top_story.link):
        print("⏩ No new article. Skipping...")
        return
    
    summary = summarize_article(top_story.title, top_story.link, top_story.description)
    
    post_body = f"""
    <h2>{top_story.title}</h2>
    <p>{summary}</p>
    <p>Source: <a href="{top_story.link}">{top_story.link}</a></p>
    """
    
    publish_to_squarespace(top_story.title, post_body)
    save_posted(top_story.link)

# ===== RUN BOT =====
if __name__ == "__main__":
    run_bot()
