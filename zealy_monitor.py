import asyncio
import json
import os
import time
import hashlib
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

URL = "https://zealy.io/cw/dexifier/questboard"
DATA_FILE = "dexifier_quests.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def hash_quest(text):
    """Generate SHA256 hash of a quest title."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def fetch_quests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_timeout(10000)  # wait 10s for JavaScript to render
        content = await page.content()
        soup = BeautifulSoup(content, "html.parser")
        await browser.close()

        quest_cards = soup.select("div.py-quest-card-xxl-y")
        quest_titles = []
        for card in quest_cards:
            title = card.get_text(strip=True)
            if title and title not in quest_titles:
                quest_titles.append(title)

        return quest_titles


def load_previous_hashes():
    if not os.path.exists(DATA_FILE):
        return set()
    with open(DATA_FILE, "r") as f:
        return set(json.load(f))


def save_current_hashes(hashes):
    with open(DATA_FILE, "w") as f:
        json.dump(list(hashes), f)


def send_telegram_alert(new_quests):
    message = "🆕 New quests on Dexifier Zealy board:\n\n"
    message += "\n".join(f"🔸 {q}" for q in new_quests)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print("Telegram Error:", response.text)
    except Exception as e:
        print("Telegram Exception:", e)


async def main():
    current_quests = await fetch_quests()
    print("📋 Fetched quests:", current_quests)

    current_hashes = {hash_quest(q): q for q in current_quests}
    previous_hashes = load_previous_hashes()

    new_hashes = set(current_hashes.keys()) - previous_hashes
    new_quests = [current_hashes[h] for h in new_hashes]

    if new_quests:
        print("🔔 New quests detected!")
        for q in new_quests:
            print("➤", q)
        send_telegram_alert(new_quests)

        # Save the updated set of hashes
        save_current_hashes(set(current_hashes.keys()))
    else:
        print("✅ No new quests.")


if __name__ == "__main__":
    while True:
        asyncio.run(main())
