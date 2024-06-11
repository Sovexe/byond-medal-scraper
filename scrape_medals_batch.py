import requests
from bs4 import BeautifulSoup
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from tqdm import tqdm
import re

# Constants
## Delay between each batch in seconds
DELAY = 1
## Maximum number of concurrent workers
MAX_WORKERS = 10
## Delay between retries after a network failure
ERROR_DELAY = 3
## Max retries per user
RETRIES = 3
## Output file name
OUTPUT_FILE = 'all_users_medals.json'
## Input file name
INPUT_FILE = 'usernames.txt'
## Section title to search for
SECTION_TITLE = 'Space Station 13 Medals'
## Append mode: True to append with checks, False to start fresh. Allows resuming of script if only executed partway.
APPEND_MODE = False

def scrape_medals(user, retries=RETRIES):
    url = f"https://www.byond.com/members/{user}?tab=medals&all=1"
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            medals = []
            section_found = False
            for section in soup.find_all('p', class_='title use_header'):
                if SECTION_TITLE in section.text:
                    section_found = True
                    table_row = section.find_next('tr')
                    while table_row:
                        for medal_td in table_row.find_all('td', style='vertical-align:top;text-align:center;'):
                            name = medal_td.find('span', class_='medal_name').text.strip()
                            date_str = medal_td.find('p', class_='smaller').text.replace('Earned ', '').strip()
                            date_str = re.sub(r'\s+', ' ', date_str)  # Remove multiple spaces
                            date = parse_date(date_str)
                            medals.append({'Name': name, 'Date': date})
                        table_row = table_row.find_next_sibling('tr')
                    break
            if not section_found:
                log_error(user, f"Section '{SECTION_TITLE}' not found")
                
            return {user: medals}
        except (requests.exceptions.RequestException, AttributeError) as e:
            time.sleep(ERROR_DELAY)
            if attempt == retries - 1:
                log_error(user, str(e))
                return {}

def parse_date(date_str):
    # Clean non-breaking spaces and HTML entities
    date_str = date_str.replace('\u00a0', ' ')
    date_str = re.sub(r'\s+', ' ', date_str).strip()
    
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
        elif re.match(r"^on \w+day, \d+:\d+ [ap]m$", date_str):
            # Handle 'on <day of the week>, <time>'
            parts = date_str.split(', ')
            day_of_week = parts[0].split(' ')[1]
            time_str = parts[1]
            now = datetime.now()
            date_obj = datetime.strptime(time_str, "%I:%M %p").replace(
                year=now.year,
                month=now.month,
                day=now.day
            )
            # Adjust the day to match the correct day of the week
            while date_obj.strftime('%A') != day_of_week:
                date_obj -= timedelta(days=1)
        elif date_str.startswith("on"):
            try:
                date_obj = datetime.strptime(date_str, "on %b %d %Y, %I:%M %p")
            except ValueError:
                date_obj = datetime.strptime(date_str, "on %b %d, %I:%M %p").replace(year=datetime.now().year)
        else:
            date_obj = datetime.strptime(date_str, "on %b %d %Y, %I:%M %p")
        return date_obj.isoformat()
    except ValueError:
        log_error('Unknown', f"Failed to parse date string: {date_str}")
        return date_str

def save_batch_to_json(batch_data, filename):
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            existing_data = json.load(f)
        existing_data.update(batch_data)
        with open(filename, 'w') as f:
            json.dump(existing_data, f, indent=4)
    else:
        with open(filename, 'w') as f:
            json.dump(batch_data, f, indent=4)

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
    
    with open(INPUT_FILE, 'r') as f:
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
    
    # Process users in batches
    for i in tqdm(range(0, len(usernames_to_process), MAX_WORKERS), desc="Processing batches"):
        batch = usernames_to_process[i:i + MAX_WORKERS]
        batch_results = {}
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(scrape_medals, user): user for user in batch}
            
            for future in as_completed(futures):
                user = futures[future]
                try:
                    result = future.result()
                    if result:
                        batch_results.update(result)
                except Exception as e:
                    log_error(user, str(e))
        
        # Save the batch to disk
        save_batch_to_json(batch_results, OUTPUT_FILE)
        
        # Delay after processing each batch
        time.sleep(DELAY)
    
    elapsed_time = time.time() - start_time
    print(f"Script completed in {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()
