import json
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JSON_PATH = "data/perks.json"

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
        perks_data = json.load(f)

    print(f"Syncing {len(perks_data)} perks to Supabase...")

    # 2. Prepare the data for Batch Upsert
    upsert_list = []

    for slug, data in perks_data.items():
        icon_url = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/assets/perks/{data['icon_file']}"

        upsert_list.append({
            "name": data["name"],
            "side": data["side"],
            "description": data["description"],
            "tier_values": data["tier_values"],
            "icon_url": icon_url
        })

    try:
        # 3. Perform the Upsert
        result = supabase.table("perks").upsert(upsert_list, on_conflict="name").execute()
        
        if result.data:
            print(f"Successfully synced {len(result.data)} perks to the database!")
        
    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == "__main__":
    sync_perks()