import praw
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
    try:
        subreddit = reddit.subreddit(subreddit_name)
        query = "timestamp:{}..{}".format(int(start_time.timestamp()), int(end_time.timestamp()))
        for attempt in range(retry_count):
            try:
                for submission in subreddit.search(query, syntax='cloudsearch', limit=None):
                    text = submission.selftext
                    for phrase in phrases_to_search:
                        if phrase in text:
                            count = text.count(phrase)
                            frequency_counter[phrase] += count
                break  # Break out of the retry loop if successful
            except praw.exceptions.APIException as e:
                if e.error_type == 'RATELIMIT':
                    sleep_time = (attempt + 1) * backoff_factor + random.uniform(0, 1)
                    print(f"Rate limit hit for subreddit '{subreddit_name}'. Sleeping for {sleep_time:.2f} seconds.")
                    time.sleep(sleep_time)
                else:
                    raise e
    except Exception as e:
        print(f"An error occurred with subreddit '{subreddit_name}': {e}")
    return frequency_counter

reddit = praw.Reddit(client_id='4YygzQy022UrJ9fdixRseA',
                     client_secret='te61CY9nVqvqIbBN7045Be18ttQTMg',
                     user_agent='mac:com.reddit_data:v1.0 (by /u/Efficient-Holiday102)')

subreddits = [
    "advice", "amitheasshole", "avengers", "bestoflegaladvice", "casualconversation", "celebhub",
    "celebs", "changemyview", "comics", "crazyideas", "doesanybodyelse", "entertainment",
    "facepalm", "harrypotter", "howtonotgiveafuck", "joerogan", "kanye", "kendricklamar",
    "legaladvice", "lotr", "makenewfriendshere", "marvel", "movies", "music", "needadvice",
    "quotes", "raisedbynarcissists", "scifi", "showerthoughts", "skateboarding", "starwars",
    "tipofmytongue", "toastme", "tinder", "investing", "stocks", "economics", "stockmarket",
    "economy", "globalmarkets", "wallstreetbets", "options", "finance", "bitcoin", "dividends",
    "cryptocurrency", "securityanalysis", "algotrading", "daytrading", "pennystocks", "valueinvesting",
    "middleclassfinance", "povertyfinance", "personalfinance", "financialplanning", "frugal",
    "financialindependence", "careerguidance", "leanfire", "fatfire", "childfree",
    "realestateinvesting", "personalfinancecanada", "fire", "robinhood", "1910s", "1920s", "1930s",
    "1940s", "1950s", "1960s", "1970s", "1980s", "80s", "1990s", "40something", "AskOldPeople",
    "BoomTimes", "caregiving", "GetOffMyLawn", "MidCentury", "nostalgia", "off_lawn",
    "OlderRedditors", "Over30Reddit", "OverFifty", "RedditForGrownups", "Seniors", "seventies",
    "Sixties", "Oldschoolcool", "Retirement", "Over60", "AskOldPeopleAdvice"
]

phrases_to_search = []
for i in range(1, 71):
    phrases_to_search.append("{} day".format(i))
numeric_strings = [re.findall(r'\b(\d+\sday)s?\b', phrase)[0] for phrase in phrases_to_search]

p = inflect.engine()
word_representations = [p.number_to_words(int(re.search(r'\d+', phrase).group())) + " " + re.search(r'\w+$', phrase).group() for phrase in numeric_strings]

output_file_path = 'probability_phrase_frequencies.xlsx'
workbook = Workbook()
workbook.remove(workbook.active)  # Remove the default sheet

start_year = 2005
end_year = 2023  # Adjust this to the current or desired year
timeframes = get_yearly_timeframes(start_year, end_year)

def process_timeframe(timeframe):
    start_time, end_time = timeframe
    frequency_counter = Counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scrape_subreddit, subreddit, start_time, end_time, phrases_to_search) for subreddit in subreddits]
        for future in futures:
            frequency_counter.update(future.result())
    return start_time, end_time, frequency_counter

with ThreadPoolExecutor(max_workers=2) as executor:
    results = executor.map(process_timeframe, timeframes)

for start_time, end_time, frequency_counter in results:
    sheet_name = f"{start_time.year}-{end_time.year - 1}"
    worksheet = workbook.create_sheet(title=sheet_name)
    worksheet.append(['String', 'Frequency'])

    combined_items = [(phrase, frequency_counter[phrase]) for phrase in phrases_to_search]
    sorted_combined_items = sorted(combined_items, key=lambda item: (sort_key(item[0]), item[0]))

    for item, frequency in sorted_combined_items:
        worksheet.append([item, frequency])

workbook.save(output_file_path)

print("probability_phrase_frequencies.xlsx")
