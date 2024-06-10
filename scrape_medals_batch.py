import requests
from bs4 import BeautifulSoup
import json
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

def scrape_medals(user, retries=3):
    url = f"https://www.byond.com/members/{user}?tab=medals&all=1"
    for attempt in range(retries):
        try:
            print(f"Scraping {user}, attempt {attempt + 1}")
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            medals = []
            for medal in soup.find_all('td', style='vertical-align:top;text-align:center;'):
                name = medal.find('span', class_='medal_name').text.strip()
                date_str = medal.find('p', class_='smaller').text.replace('Earned ', '').strip()
                date = parse_date(date_str)
                medals.append({'Name': name, 'Date': date})
            
            print(f"Successfully scraped {user}")
            return {user: medals}
        except (requests.exceptions.RequestException, AttributeError) as e:
            print(f"Error scraping {user} on attempt {attempt + 1}: {e}")
            time.sleep(5)  # wait for 5 seconds before retrying
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
        print(f"Date parsing failed for: {date_str}")
        return date_str

def save_to_json(data, filename):
    if data:
        if not os.path.isfile(filename):
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
        else:  # Append to existing file
            with open(filename, 'r') as f:
                existing_data = json.load(f)
            existing_data.update(data)
            with open(filename, 'w') as f:
                json.dump(existing_data, f, indent=4)
        print(f'Saved to {filename}')
    else:
        print("No data to save.")

def log_error(user, error):
    with open('error_log.txt', 'a') as f:
        f.write(f"Error for {user}: {error}\n")
    print(f"Logged error for {user}")

def main():
    with open('usernames.txt', 'r') as f:
        usernames = [line.strip() for line in f]
    
    all_medals = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = {executor.submit(scrape_medals, user): user for user in usernames}
        
        for future in as_completed(future_to_user):
            user = future_to_user[future]
            try:
                medals = future.result()
                if medals:
                    all_medals.update(medals)
            except Exception as e:
                print(f"Exception occurred while scraping {user}: {e}")
                log_error(user, str(e))
    
    if all_medals:
        save_to_json(all_medals, 'all_users_medals.json')
    else:
        print("No medals were scraped.")

if __name__ == "__main__":
    main()
