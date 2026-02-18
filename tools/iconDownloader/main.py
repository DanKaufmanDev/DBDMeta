import os
import re
import time
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SAVE_FOLDER = "DKDMeta/assets/perks"

# Headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def to_camel_case(text):
    clean = re.sub(r'[^a-zA-Z0-9 ]', '', text)
    words = clean.split()
    if not words: return ""
    return words[0].lower() + "".join(word.capitalize() for word in words[1:])

def download_icons():
    if not os.path.exists(SAVE_FOLDER):
        os.makedirs(SAVE_FOLDER)

    print("📡 Fetching icon list...")
    res = supabase.table("perks").select("name", "icon_url").not_.is_("icon_url", "null").execute()
    perks = res.data

    print(f"🚀 Found {len(perks)} icons. Downloading with rate-limit protection...")

    for perk in perks:
        name = perk['name']
        url = perk['icon_url']
        filename = f"{to_camel_case(name)}.png"
        save_path = os.path.join(SAVE_FOLDER, filename)

        # Skip if already downloaded
        if os.path.exists(save_path):
            continue

        try:
            # Added HEADERS and a timeout
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Saved: {filename}")
                # ⏳ Crucial: Wait 2 seconds between requests to avoid 429
                time.sleep(2) 
            elif response.status_code == 429:
                print(f"🛑 Rate limited on {name}. Sleeping for 30 seconds...")
                time.sleep(30)
            else:
                print(f"❌ Failed {name}: Status {response.status_code}")
        
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    download_icons()