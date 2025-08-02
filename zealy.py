import asyncio
import json
import time
import os
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

URL = "https://zealy.io/cw/dexifier/questboard"
DATA_FILE = "dexifier_quests.json"
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

async def fetch_quests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_timeout(10000)  # wait 10s for JS to render
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        await browser.close()

        quest_cards = soup.select("div[class*='QuestCard_card__']")
        quest_titles = []
        for card in quest_cards:
            title_elem = card.find('h3')
            if title_elem:
                quest_titles.append(title_elem.text.strip())
        return quest_titles

def load_previous():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_current(quests):
    with open(DATA_FILE, 'w') as f:
        json.dump(quests, f)

def send_telegram_alert(quests):
    message = "🆕 New quests on Dexifier Zealy board:\n\n"
    message += "\n".join(f"🔸 {q}" for q in quests)
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print("Telegram error:", e)

async def main():
    current_quests = await fetch_quests()
    previous_quests = load_previous()
    new_quests = [q for q in current_quests if q not in previous_quests]

    if new_quests:
        print("🔔 New quests detected!")
        for q in new_quests:
            print("➤", q)
        send_telegram_alert(new_quests)
        save_current(current_quests)
    else:
        print("✅ No new quests.")

if __name__ == "__main__":
    while True:
        asyncio.run(main())
        print("🕒 Waiting 15 minutes...")
        time.sleep(300)
