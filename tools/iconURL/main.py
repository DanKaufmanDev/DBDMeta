import os
import re
import time
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def get_variants(name):
    # Standardize names (handle common Wiki.gg naming departures)
    replacements = {
        "BBQ and Chili": "Barbecue and Chilli",
        "BBQ & Chili": "Barbecue and Chilli",
        "BBQ": "Barbecue and Chilli"
    }
    name = replacements.get(name, name)
    
    clean = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    words = clean.split()
    if not words: return []

    # Variants: camelCase, PascalCase, and lowercase
    camel = words[0].lower() + "".join(w.capitalize() for w in words[1:])
    pascal = "".join(w.capitalize() for w in words)
    lower = "".join(w.lower() for w in words)
    
    return list(set([camel, pascal, lower]))

def sync_icons_final_attempt():
    res = supabase.table("perks").select("name").is_("icon_url", "null").execute()
    perks = res.data
    
    print(f"🕵️ Syncing {len(perks)} perks using Dual-Prefix logic...")

    # The two possible prefixes found in the 2026 Wiki
    prefixes = ["IconPerks", "IconsPerks"]

    for perk in perks:
        name = perk['name']
        variants = get_variants(name)
        found_url = None

        # Check every prefix against every name variant
        for prefix in prefixes:
            for v in variants:
                url = f"https://deadbydaylight.wiki.gg/images/{prefix}_{v}.png"
                try:
                    # HEAD request to keep it fast
                    if requests.head(url, timeout=3).status_code == 200:
                        found_url = url
                        break
                except:
                    continue
            if found_url: break

        if found_url:
            supabase.table("perks").update({"icon_url": found_url}).eq("name", name).execute()
            print(f"✅ FOUND: {name} -> {found_url.split('/')[-1]}")
        else:
            print(f"❌ STILL MISSED: {name}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    sync_icons_final_attempt()