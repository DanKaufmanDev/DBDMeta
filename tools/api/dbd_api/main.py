import json
import time
import undetected_chromedriver as uc
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
            // Clean up the name by removing any leftover newlines caught by the dot-all match
            const name = match[1].replace(/\\n/g, '').trim();
            
            if (['Search', 'RegisterLogin', 'General', 'Shown Stats', 'Pick Rate', 'Kill Rate'].includes(name)) continue;

            if (!seenNames.has(name) && name.length > 2) {{
                results.push({{
                    name: name,
                    pick_rate: parseFloat(match[2]),
                    // Check if group 3 exists (for Killers/Survivor perks) otherwise default to 0
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
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu") 

    print("Starting Chrome...")
    
    try:
        driver = uc.Chrome(options=options, version_main=144)
    except Exception as e:
        print(f"Version 144 init failed, attempting auto-detection: {e}")
        try:
            driver = uc.Chrome(options=options)
        except Exception as e2:
            print(f"❌ Critical Failure: Could not start Chrome. {e2}")
            sys.exit(1)
    
        # --- 1. KILLER STATS ---
        print("Fetching Killer Stats...")
        driver.get("https://nightlight.gg/killers/")
        time.sleep(5) 
        
        killer_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?(?:Kill Rate|Escape Rate)\n100%\n(\d+\.?\d*)%/gm"
        killer_stats = get_stats_from_page(driver, killer_regex)
        
        if killer_stats:
            with open("data/kmetadata.json", "w") as f:
                json.dump(killer_stats, f, indent=4)
            print(f"Captured {len(killer_stats)} Killers.")

        # --- 2. SURVIVOR PERKS ---
        print("Fetching Survivor Perks...")
        driver.get("https://nightlight.gg/perks/viewer?role=survivor&shown=pick%7Cescape_rate&sort=pick&start_days=28")
        time.sleep(5)
        
        perk_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?Escape Rate\n100%\n(\d+\.?\d*)%/gm"
        surv_perks = get_stats_from_page(driver, perk_regex)
        
        if surv_perks:
            with open("data/tsperksmetadata.json", "w") as f:
                json.dump(surv_perks, f, indent=4)
            print(f"Captured {len(surv_perks)} Survivor Perks.")

        # --- 3. KILLER PERKS ---
        print("Fetching Killer Perks...")
        driver.get("https://nightlight.gg/perks/viewer?role=killer&shown=pick&sort=pick&start_days=28")
        time.sleep(5)
        
        k_perk_regex = r"/^(.+)\n\d+ - [\d,]+ Games[\s\S]*?Pick Rate\n[\d.]+%?\n(\d+\.?\d*)%[\s\S]*?Kill Rate\n100%\n(\d+\.?\d*)%/gm"
        killer_perks = get_stats_from_page(driver, k_perk_regex)

        if killer_perks:
            with open("data/tkperksmetadata.json", "w") as f:
                json.dump(killer_perks, f, indent=4)
            print(f"Captured {len(killer_perks)} Killer Perks.")


        path = "data/tkperksmetadata.json"

        with open(path, "r") as f:
            data = json.load(f)

        for item in data:
            item['name'] = item['name'].replace('\u2019', "'").replace('\u2018', "‘").replace('\u00e2', "a")

        with open(path, "w") as f:
            json.dump(data, f, indent=4)


        path = "data/kmetadata.json"

        with open(path, "r") as f:
            data = json.load(f)

        for item in data:
            if not item['name'].startswith("The "):
                item['name'] = f"The {item['name']}"

            if item['name'] == 'Ghost Face' or 'The Ghost Face':
                item['name'] = 'The Ghostface'

        with open(path, "w") as f:
            json.dump(data, f, indent=4)


        print("JSON file cleaned and standardized.")

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    scrape_dbd_meta()