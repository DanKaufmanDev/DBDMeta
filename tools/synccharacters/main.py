import json
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JSON_PATH = "data/characters.json"

GITHUB_USER = "DanKaufmanDev"
GITHUB_REPO = "DBDMeta"
GITHUB_BRANCH = "master"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_perks():
    # 1. Load the JSON file
    if not os.path.exists(JSON_PATH):
        print(f"Error: {JSON_PATH} not found. Run your generator script first!")
        return

    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        characters = json.load(f)

    print(f"Syncing {len(characters)} characters to Supabase...")

# 2. Prepare the data for Batch Upsert
    upsert_list = []

    for slug, data in characters.items():
        role = data['role']
        
        portrait_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/assets/characters/portrait/{role.lower()}/{data['portrait_url']}"
        store_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/assets/characters/shrine/{role.lower()}/{data['store_url']}"
    
        record = {
            "name": data["name"],
            "role": role,
            "portrait_url": portrait_url,
            "store_url": store_url
        }

        if role.lower() == "killer":
            record.update({
                "speed": data.get("speed"),
                "radius": data.get("radius")
            })

        upsert_list.append(record)
            
    try:
        # 3. Perform the Upsert
        result = supabase.table("characters").upsert(upsert_list, on_conflict="name").execute()
        
        if result.data:
            print(f"Successfully synced {len(result.data)} characters to the database!")
        
    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == "__main__":
    sync_perks()