import requests
from bs4 import BeautifulSoup
import os
import json

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')
STATE_FILE = 'last_intel.json'

def fetch_official_site():
    """Scrapes multiple recent articles from the official site."""
    try:
        url = "https://deadbydaylight.com/news/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        # Find the first 5 news links
        links = soup.find_all('a', href=True, class_=lambda x: x and 'news' in x)[:5]
        
        for link in links:
            articles.append({
                "source": "Official Site",
                "id": link['href'].split('/')[-1],
                "title": link.get_text(strip=True),
                "url": "https://deadbydaylight.com" + link['href'],
                "color": 15548997
            })
        return articles
    except Exception as e:
        print(f"Official site error: {e}")
        return []

def fetch_steam_news():
    """Fetches the last 5 news items from Steam API."""
    try:
        url = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=381210&count=5"
        response = requests.get(url, timeout=10)
        items = response.json()['appnews']['newsitems']
        
        return [{
            "source": "Steam Community",
            "id": str(item['gid']),
            "title": item['title'],
            "url": item['url'],
            "color": 1752220
        } for item in items]
    except Exception as e:
        print(f"Steam error: {e}")
        return []

def main():
    # 1. Load existing history
    history = {}
    is_first_run = not os.path.exists(STATE_FILE)
    
    if not is_first_run:
        with open(STATE_FILE, 'r') as f:
            history = json.load(f)

    sources = [fetch_official_site, fetch_steam_news]
    
    for fetch_func in sources:
        current_articles = fetch_func()
        if not current_articles: continue
        
        source_name = current_articles[0]['source']
        if source_name not in history:
            history[source_name] = []

        for article in current_articles:
            # 2. Compare against history
            if article['id'] not in history[source_name]:
                
                # Only ping Discord if it's NOT the very first time running the script
                if not is_first_run:
                    print(f"NEW INTEL: {article['title']}")
                    payload = {
                        "username": "THE ENTITY",
                        "avatar_url": "https://raw.githubusercontent.com/DanKaufmanDev/DBDMeta/master/assets/ui/DBDMLogo.webp",
                        "embeds": [{
                            "title": f"[{article['source'].upper()}] {article['title']}",
                            "url": article['url'],
                            "description": "A new transmission has been intercepted from the fog.",
                            "color": article['color']
                        }]
                    }
                    requests.post(WEBHOOK_URL, json=payload)
                
                # Add to history so we don't ping again
                history[source_name].append(article['id'])

    # 3. Save updated state (keeping only last 20 IDs per source to keep file small)
    for source in history:
        history[source] = history[source][-20:]

    with open(STATE_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    if is_first_run:
        print("Seed run complete. History populated without pings.")

if __name__ == "__main__":
    main()