import json
import time
import os
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Zealy Dexifier board URL
URL = "https://zealy.io/cw/dexifier/questboard"
DATA_FILE = "dexifier_quests.json"

# Telegram config
BOT_TOKEN = "8458020387:AAEU4X6pIQHQHUmY6Yp8hNwpxXZSKcFHPf8"
CHAT_ID = "6841022258"

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=chrome_options)

def fetch_quests():
    driver = setup_driver()
    driver.get(URL)
    time.sleep(10)  # wait for full JS render
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

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
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Telegram error:", e)

def main():
    current_quests = fetch_quests()
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
    main()
