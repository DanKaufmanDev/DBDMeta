import json
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# --- Configuration ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def sync_to_supabase(file_path, table_name):
    if not os.path.exists(file_path):
        print(f"Skipping: {file_path} (File not found)")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"Syncing {len(data)} rows to {table_name}...")

    for item in data:
        payload = {
            "name": item["name"],
            "pick_rate": item["pick_rate"],
            "kill_rate_or_escape": item.get("kill_rate_or_escape", 0),
        }

        try:
            supabase.table(table_name).upsert(payload, on_conflict="name").execute()
        except Exception as e:
            print(f"Error syncing {item['name']}: {e}")

if __name__ == "__main__":
    sync_to_supabase("data/kmetadata.json", "characters")
    sync_to_supabase("data/tkperksmetadata.json", "perks")
    sync_to_supabase("data/tsperksmetadata.json", "perks")
    print("Sync complete. Current tables are up to date.")