import requests
import re
from collections import Counter
from openpyxl import Workbook
import inflect
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time
import random

def sort_key(item):
    match = re.search(r'\d+', item)
    if match:
        return int(match.group())
    else:
        return float('inf')

def get_yearly_timeframes(start_year, end_year):
    timeframes = []
    for year in range(start_year, end_year):
        start_time = datetime(year, 1, 1)
        end_time = datetime(year + 1, 1, 1)
        timeframes.append((start_time, end_time))
    return timeframes

def scrape_subreddit(subreddit_name, start_time, end_time, phrases_to_search, retry_count=5, backoff_factor=1):
    frequency_counter = Counter()
    base_url = "https://api.pushshift.io/reddit/search/submission"
    params = {
        'subreddit': subreddit_name,
        'after': int(start_time.timestamp()),
        'before': int(end_time.timestamp()),
        'size': 500
    }

    for attempt in range(retry_count):
        try:
            response = requests.get(base_url, params=params)
            if response.status_code == 429:  # Too Many Requests
                sleep_time = (attempt + 1) * backoff_factor + random.uniform(0, 1)
                print(f"Rate limit hit for subreddit '{subreddit_name}'. Sleeping for {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                continue
            response.raise_for_status()
            data = response.json().get('data', [])
            for submission in data:
                text = submission.get('selftext', '')
                for phrase in phrases_to_search:
                    if phrase in text:
                        count = text.count(phrase)
                        frequency_counter[phrase] += count
            break  # Break out of the retry loop if successful
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for subreddit '{subreddit_name}': {e}")
            if attempt < retry_count - 1:
                sleep_time = (attempt + 1) * backoff_factor + random.uniform(0, 1)
                print(f"Retrying in {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
    return frequency_counter

subreddit = "advice"
phrases_to_search = [f"{i} day" for i in range(1, 31)]

p = inflect.engine()
word_representations = [p.number_to_words(i) + " day" for i in range(1, 31)]

output_file_path = 'advice_phrase_frequencies.xlsx'
workbook = Workbook()
workbook.remove(workbook.active)  # Remove the default sheet

start_year = 2010
end_year = 2023  # Adjust this to the current or desired year
timeframes = get_yearly_timeframes(start_year, end_year)

def process_timeframe(timeframe):
    start_time, end_time = timeframe
    frequency_counter = Counter()
    frequency_counter.update(scrape_subreddit(subreddit, start_time, end_time, phrases_to_search))
    return start_time, end_time, frequency_counter

results = map(process_timeframe, timeframes)

for start_time, end_time, frequency_counter in results:
    sheet_name = f"{start_time.year}"
    worksheet = workbook.create_sheet(title=sheet_name)
    worksheet.append(['String', 'Frequency'])

    combined_items = [(phrase, frequency_counter[phrase]) for phrase in phrases_to_search]
    sorted_combined_items = sorted(combined_items, key=lambda item: (sort_key(item[0]), item[0]))

    for item, frequency in sorted_combined_items:
        worksheet.append([item, frequency])

workbook.save(output_file_path)

print("advice_phrase_frequencies.xlsx")
