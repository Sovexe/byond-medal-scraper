import requests
from bs4 import BeautifulSoup
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from tqdm import tqdm

# Delay between each batch in seconds
DELAY = 1
# Maximum number of concurrent workers
MAX_WORKERS = 10
# Delay between retries after a network failure
ERROR_DELAY = 3
# Max retries per user
RETRIES = 3
# Output file name
OUTPUT_FILE = 'all_users_medals.json'
# Append mode: True to append with checks, False to start fresh. Allows resuming of script if only executed partway.
APPEND_MODE = False

def scrape_medals(user, retries=RETRIES):
    url = f"https://www.byond.com/members/{user}?tab=medals&all=1"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            medals = []
            for medal in soup.find_all('td', style='vertical-align:top;text-align:center;'):
                name = medal.find('span', class_='medal_name').text.strip()
                date_str = medal.find('p', class_='smaller').text.replace('Earned ', '').strip()
                date = parse_date(date_str)
                medals.append({'Name': name, 'Date': date})
            
            return {user: medals}
        except (requests.exceptions.RequestException, AttributeError) as e:
            time.sleep(ERROR_DELAY)
            if attempt == retries - 1:
                log_error(user, str(e))
                return {}

def parse_date(date_str):
    try:
        if date_str.startswith("at"):
            date_obj = datetime.strptime(date_str, "at %I:%M %p").replace(
                year=datetime.now().year,
                month=datetime.now().month,
                day=datetime.now().day
            )
        elif date_str.startswith("yesterday"):
            date_str = date_str.replace("yesterday,", "").strip()
            date_obj = datetime.strptime(date_str, "%I:%M %p").replace(
                year=(datetime.now() - timedelta(days=1)).year,
                month=(datetime.now() - timedelta(days=1)).month,
                day=(datetime.now() - timedelta(days=1)).day
            )
        else:
            try:
                date_obj = datetime.strptime(date_str, "on %b %d %Y, %I:%M %p")
            except ValueError:
                date_obj = datetime.strptime(date_str, "on %b %d, %I:%M %p").replace(year=datetime.now().year)
        return date_obj.isoformat()
    except ValueError:
        return date_str

def save_to_json(data, filename):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            existing_data = json.load(f)
        existing_data.update(data)
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=4)
    else:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

def log_error(user, error):
    with open('error_log.txt', 'a') as f:
        f.write(f"Error for {user}: {error}\n")

def load_existing_data(filename):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def main():
    start_time = time.time()
    
    with open('usernames.txt', 'r') as f:
        usernames = [line.strip() for line in f]

    if not APPEND_MODE:
        if os.path.isfile(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)
        processed_users = set()
        usernames_to_process = usernames
    else:
        existing_data = load_existing_data(OUTPUT_FILE)
        processed_users = set(existing_data.keys())
        usernames_to_process = [user for user in usernames if user not in processed_users]
    
    all_medals = {}
    
    # Process users in batches
    for i in tqdm(range(0, len(usernames_to_process), MAX_WORKERS), desc="Processing batches"):
        batch = usernames_to_process[i:i + MAX_WORKERS]
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(scrape_medals, user): user for user in batch}
            
            for future in as_completed(futures):
                user = futures[future]
                try:
                    result = future.result()
                    if result:
                        all_medals.update(result)
                        save_to_json(result, OUTPUT_FILE)
                except Exception as e:
                    log_error(user, str(e))
        
        # Delay after processing each batch
        time.sleep(DELAY)
    
    elapsed_time = time.time() - start_time
    print(f"Script completed in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
