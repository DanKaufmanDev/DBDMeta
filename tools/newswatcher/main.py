import requests
from bs4 import BeautifulSoup
import os
import json

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STATE_FILE = 'last_intel.json'

def fetch_official_site():
    """Scrapes the official DBD news page."""
    try:
        url = "https://deadbydaylight.com/news/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        first_article = soup.find('a', href=True, class_=lambda x: x and 'news' in x)
        if not first_article: return None

        return {
            "source": "Official Site",
            "id": first_article['href'].split('/')[-1],
            "title": first_article.get_text(strip=True),
            "url": "https://deadbydaylight.com" + first_article['href'],
            "color": 15548997
        }
    except Exception as e:
        print(f"Official site error: {e}")
        return None

def fetch_steam_news():
    """Scrapes the Steam Community Hub for DBD."""
    try:
        url = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=381210&count=10"
        response = requests.get(url, timeout=10)
        item = response.json()['appnews']['newsitems'][0]
        
        return {
            "source": "Steam Community",
            "id": str(item['gid']),
            "title": item['title'],
            "url": item['url'],
            "color": 1752220 
        }
    except Exception as e:
        print(f"Steam error: {e}")
        return None

def main():
    
    history = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            history = json.load(f)

    
    sources = [fetch_official_site, fetch_steam_news]
    new_intel_found = False

    for fetch_func in sources:
        news = fetch_func()
        if not news: continue

        source_name = news['source']
        
        
        if history.get(source_name) == news['id']:
            print(f"No new intel from {source_name}.")
            continue

        
        print(f"New Intel from {source_name}: {news['title']}")
        new_intel_found = True
        
        payload = {
            "username": "THE ENTITY",
            "avatar_url": "https://raw.githubusercontent.com/DanKaufmanDev/DBDMeta/master/assets/ui/DBDMLogo.webp",
            "embeds": [{
                "title": f"[{news['source'].upper()}] {news['title']}",
                "url": news['url'],
                "description": "A new transmission has been intercepted from the fog.",
                "color": news['color'],
                "footer": {"text": f"ID: {news['id']}"}
            }]
        }
        
        requests.post(WEBHOOK_URL, json=payload)
        history[source_name] = news['id']

    
    if new_intel_found:
        with open(STATE_FILE, 'w') as f:
            json.dump(history, f)

if __name__ == "__main__":
    main()