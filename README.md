# BYOND Medals Scraper

This script scrapes medals earned by BYOND users and saves the data in JSON format. It handles different date formats and converts them to ISO 8601 format.

## Features

- Scrapes medals for a list of BYOND usernames
- Handles date formats: today, yesterday, on DAY, and specific dates
- Saves data in JSON format
- Supports concurrent scraping for faster execution
- Includes a progress bar to show scraping progress
- Adds a delay between batches to be considerate to the web server
- Can resume scraping from where it left off if interrupted

## Requirements

- Python 3.x
- `requests` library
- `beautifulsoup4` library
- `tqdm` library

## Installation

1. Clone this repository:

    ```bash
    git clone https://github.com/yourusername/byond-medals-scraper.git
    cd byond-medals-scraper
    ```

2. Create a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    ```

3. Activate the virtual environment:

    - On Windows:
      ```bash
      venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```

4. Install the required libraries:

    ```bash
    pip install -r requirements.txt
    ```

    Ensure your `requirements.txt` contains the following:
    ```
    requests
    beautifulsoup4
    tqdm
    ```

## Usage

1. Create a `usernames.txt` file in the same directory as the script. This file should contain one username per line.

    Example `usernames.txt`:
    ```
    user1
    user2
    user3
    ```

2. Set the desired mode and parameters at the top of the script:
    - `DELAY`: Delay between each batch in seconds. Default is `1`.
    - `MAX_WORKERS`: Maximum number of concurrent workers. Default is `10`.
    - `ERROR_DELAY`: Delay between retries after a network failure. Default is `3`.
    - `RETRIES`: Max retries per user. Default is `3`.
    - `OUTPUT_FILE`: Output file name. Default is `'all_users_medals.json'`.
    - `INPUT_FILE`: Input file name. Default is `'usernames.txt'`.
    - `SECTION_TITLE`: Section title to search for. Default is `'Space Station 13 Medals'`.
    - `APPEND_MODE`: Boolean to either append with checks (`True`) or start fresh (`False`). Default is `False`.

3. Run the script:

    ```bash
    python scrape_medals_batch.py
    ```

4. The script will create a `all_users_medals.json` file containing the scraped data. Errors will be logged in `error_log.txt`.

## Example Output

Example JSON structure:
```json
{
    "user1": [
        {
            "Name": "Fish",
            "Date": "2023-11-29T10:22:00"
        },
        {
            "Name": "It'sa me, Mario",
            "Date": "2023-11-29T10:23:00"
        }
    ],
    "user2": [
        {
            "Name": "HIGH VOLTAGE",
            "Date": "2023-11-29T10:34:00"
        }
    ]
}
