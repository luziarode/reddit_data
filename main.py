import praw
import csv
import json

# Authenticate your application
reddit = praw.Reddit(client_id='4YygzQy022UrJ9fdixRseA',
                     client_secret='te61CY9nVqvqIbBN7045Be18ttQTMg',
                     user_agent='mac:com.reddit_data:v1.0 (by /u/Efficient-Holiday102)')

# Define the subreddit you want to scrape
subreddit = reddit.subreddit('AmItheAsshole')

reddit_data = []

# Iterate through submissions
for submission in subreddit.hot(limit=200): # Adjust the limit as needed
    submission_info = {
        "title": submission.title,
        "text": submission.selftext
    }
    reddit_data.append(submission_info)

# Store data in a CSV file
csv_file_path = 'reddit_data.csv'
with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
    fieldnames = ['title', 'text']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()
    for submission_info in reddit_data:
        writer.writerow(submission_info)