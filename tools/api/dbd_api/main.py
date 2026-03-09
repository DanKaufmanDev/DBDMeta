import json
import time
import sys
import os
import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
    
def get_stats_from_page(driver, regex_pattern):
    """Utility to run the regex extraction on the current page text."""
    return driver.execute_script(f"""
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

def scrape_dbd_meta():
    driver = None
    options = uc.ChromeOptions()
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    print("Starting Stealth Chrome...")
    try:
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=145)
        
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
    except Exception as e:
        print(f"Critical Failure: Could not start Chrome. {e}")
        sys.exit(1)
    
    try:
        def wait_for_data():
            """Enhanced wait logic to handle Cloudflare challenges."""
            print(f"Waiting for page content... (Current Title: {driver.title})")
            
            if "Just a moment" in driver.title or "Cloudflare" in driver.page_source:
                print("Cloudflare challenge detected. Waiting 20 seconds for auto-solve...")
                time.sleep(20)
            
            try:
                WebDriverWait(driver, 45).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
                time.sleep(3) 
                print("Content successfully loaded.")
            except Exception:
                print(f"Timed out or Cloudflare blocked. Title: {driver.title}")
                driver.save_screenshot("data/error.png")

        os.makedirs("data", exist_ok=True)

        # --- 1. KILLER STATS ---
        print("Fetching Killer Stats...")
        driver.get("https://nightlight.gg/killers/")
        wait_for_data()
        
        killer_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?(?:Kill Rate|Escape Rate)\n100%\n(\d+\.?\d*)%/gm"
        killer_stats = get_stats_from_page(driver, killer_regex)
        
        if killer_stats:
            with open("data/kmetadata.json", "w") as f:
                json.dump(killer_stats, f, indent=4)
            print(f"Captured {len(killer_stats)} Killers.")

        # --- 2. SURVIVOR PERKS ---
        print("Fetching Survivor Perks...")
        driver.get("https://nightlight.gg/perks/viewer?role=survivor")
        wait_for_data()
        
        perk_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?Escape Rate\n100%\n(\d+\.?\d*)%/gm"
        surv_perks = get_stats_from_page(driver, perk_regex)
        
        if surv_perks:
            with open("data/tsperksmetadata.json", "w") as f:
                json.dump(surv_perks, f, indent=4)
            print(f"Captured {len(surv_perks)} Survivor Perks.")

        # --- 3. KILLER PERKS ---
        print("Fetching Killer Perks...")
        driver.get("https://nightlight.gg/perks/viewer?role=killer")
        wait_for_data()
        
        k_perk_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%/gm"
        killer_perks = get_stats_from_page(driver, k_perk_regex)

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
        print(f"Error during scraping: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    scrape_dbd_meta()