import json
import os
import sys
from seleniumbase import SB

def scrape_dbd_meta():
    with SB(uc=True, xvfb=True) as sb:
        
        def fetch_and_extract(url, name_for_log, regex_pattern):
            print(f"Navigating to {url}...")
            sb.uc_open_with_reconnect(url, reconnect_time=4)
            
            sb.uc_gui_click_captcha()

            try:
                sb.wait_for_element("main", timeout=25)
            except:
                print(f"Failed to bypass Cloudflare on {name_for_log}. Title: {sb.get_title()}")
                sb.save_screenshot(f"data/error_{name_for_log}.png")
                return None

            return sb.execute_script(f"""
                const text = document.body.innerText;
                const results = [];
                const seenNames = new Set();
                const regex = {regex_pattern};
                let match;
                while ((match = regex.exec(text)) !== null) {{
                    const name = match[1].replace(/\\n/g, '').trim();
                    if (['Search', 'RegisterLogin', 'General', 'Shown Stats', 'Pick Rate', 'Kill Rate'].includes(name)) continue;
                    if (!seenNames.has(name) && name.length > 2) {{
                        results.push({{
                            name: name,
                            pick_rate: parseFloat(match[2]),
                            kill_rate_or_escape: match[3] ? parseFloat(match[3]) : 0
                        }});
                        seenNames.add(name);
                    }}
                }}
                return results;
            """)

        os.makedirs("data", exist_ok=True)

        try:
            # --- 1. KILLERS ---
            k_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?(?:Kill Rate|Escape Rate)\n100%\n(\d+\.?\d*)%/gm"
            killer_stats = fetch_and_extract("https://nightlight.gg/killers/", "killers", k_regex)
            if killer_stats:
                with open("data/kmetadata.json", "w") as f:
                    json.dump(killer_stats, f, indent=4)
                print(f"Captured {len(killer_stats)} Killers.")

            # --- 2. SURVIVOR PERKS ---
            s_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?Escape Rate\n100%\n(\d+\.?\d*)%/gm"
            surv_perks = fetch_and_extract("https://nightlight.gg/perks/viewer?role=survivor", "surv_perks", s_regex)
            if surv_perks:
                with open("data/tsperksmetadata.json", "w") as f:
                    json.dump(surv_perks, f, indent=4)
                print(f"Captured {len(surv_perks)} Survivor Perks.")

            # --- 3. KILLER PERKS ---
            kp_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%/gm"
            killer_perks = fetch_and_extract("https://nightlight.gg/perks/viewer?role=killer", "killer_perks", kp_regex)
            if killer_perks:
                with open("data/tkperksmetadata.json", "w") as f:
                    json.dump(killer_perks, f, indent=4)
                print(f"Captured {len(killer_perks)} Killer Perks.")

            # --- CLEANING LOGIC ---
            print("Cleaning JSON files...")
            
            def clean_perk_names(file_path):
                if not os.path.exists(file_path): return
                with open(file_path, "r") as f:
                    data = json.load(f)
                for item in data:
                    item['name'] = item['name'].replace('\u2019', "'").replace('\u2018', "\u2018").replace('\u00e2', "a")
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=4)

            clean_perk_names("data/tkperksmetadata.json")
            clean_perk_names("data/tsperksmetadata.json")

            if os.path.exists("data/kmetadata.json"):
                with open("data/kmetadata.json", "r") as f:
                    k_data = json.load(f)
                for item in k_data:
                    if item['name'] in ['Ghost Face', 'The Ghost Face']:
                        item['name'] = 'The Ghostface'
                    elif not item['name'].startswith("The "):
                        item['name'] = f"The {item['name']}"
                
                with open("data/kmetadata.json", "w") as f:
                    json.dump(k_data, f, indent=4)

            print("JSON files cleaned and standardized.")

        except Exception as e:
            print(f"Error during scraping or cleaning: {e}")

if __name__ == "__main__":
    scrape_dbd_meta()