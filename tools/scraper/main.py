import os
import time
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_complete_perk_list():
    print("📡 Deep Scanning all Perk Categories for 2026 content...")
    api_url = "https://deadbydaylight.wiki.gg/api.php"
    
    # These three categories cover 100% of the 315 perks
    target_cats = ["Category:Survivor_Perks", "Category:Killer_Perks", "Category:General_Perks"]
    all_titles = set()

    for cat in target_cats:
        cmcontinue = None
        while True:
            params = {
                "action": "query", "list": "categorymembers",
                "cmtitle": cat, "cmlimit": "500", "format": "json", "cmcontinue": cmcontinue
            }
            res = requests.get(api_url, params=params).json()
            batch = [item['title'] for item in res['query']['categorymembers'] if ":" not in item['title']]
            all_titles.update(batch)
            cmcontinue = res.get("continue", {}).get("cmcontinue")
            if not cmcontinue: break

    return sorted(list(all_titles))

def scrape_all_perks():
    titles = get_complete_perk_list()
    total = len(titles)
    print(f"✅ Target acquired: {total} unique perks found. Commencing final sync...")
    
    all_data = []
    api_url = "https://deadbydaylight.wiki.gg/api.php"

    for i in range(0, total, 40):
        chunk = titles[i:i+40]
        params = {
            "action": "query", "prop": "extracts|categories",
            "titles": "|".join(chunk), "exintro": "1", "explaintext": "1",
            "redirects": "1", "cllimit": "max", "format": "json"
        }
        
        try:
            res = requests.get(api_url, params=params).json()
            pages = res.get('query', {}).get('pages', {})
            
            for page_data in pages.values():
                if 'extract' in page_data:
                    title = page_data['title']
                    extract = page_data['extract'].strip()
                    cats = str(page_data.get('categories', []))
                    
                    side = "Killer" if "Killer Perks" in cats else "Survivor"
                    
                    all_data.append({
                        "name": title,
                        "description": extract,
                        "side": side,
                        "primary_tag": "General" if "General Perks" in cats else "Unique"
                    })
            time.sleep(1)
            print(f"📦 Progress: {min(i+40, total)}/{total}")
        except Exception as e:
            print(f"⚠️ Error: {e}")

    if all_data:
        # Upserting with name as the key to prevent duplicates
        supabase.table("perks").upsert(all_data, on_conflict="name").execute()
        print(f"🎉 FINAL SYNC COMPLETE. Database total: {len(all_data)}")

if __name__ == "__main__":
    scrape_all_perks()