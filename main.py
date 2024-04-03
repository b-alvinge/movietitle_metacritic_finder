import requests
from bs4 import BeautifulSoup
import pandas as pd

from selenium import webdriver
import time
import phonetics
from fuzzywuzzy import fuzz

from selenium.common import NoSuchElementException

import inflect
import re
import os

# Initialize the inflect engine for converting numbers to words
p = inflect.engine()

# Function to convert numbers in a string to words
def numbers_to_words(input_str):
    # Find all numbers in the string
    numbers = re.findall(r'\b\d+\b', input_str)
    for number in numbers:
        # Convert each number to words
        words = p.number_to_words(number)
        # Replace the number with its word equivalent in the string
        input_str = input_str.replace(number, words, 1)
    return input_str

# Function to normalize and get phonetic code
def get_phonetic_code(input_str):
    # Convert numbers to words in the string
    words_str = numbers_to_words(input_str)
    # Normalize the string (e.g., to lowercase)
    normalized_str = words_str.lower()
    # Get double metaphone codes
    phonetic_code = phonetics.dmetaphone(normalized_str)
    return phonetic_code


def get_metacritic_info(movie_title):
    # Replace spaces with '+' for URL encoding
    if movie_title.endswith(', The'):
        movie_title = "The " + movie_title[:-5]
    search_query = movie_title.lower().replace(' ', '-')

    # Construct the search URL; you might need to adjust this based on how Metacritic's search works
    search_url = f"https://www.metacritic.com/search/{search_query}/"
    print(search_url)
    # Set a User-Agent to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0'}

    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    driver = webdriver.Chrome(options=options)
    # Fetch the search results page
    driver.get(search_url)

    try:
        element = driver.find_element("xpath", "//span[text()='Movies']")
        driver.execute_script("arguments[0].click();", element)
        time.sleep(1)
    except NoSuchElementException:
        print("Did not find the 'Movies' button.")
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.close()

    #response = requests.get(search_url, headers=headers, params=p)

    #if html.status_code == 200:
        #soup = BeautifulSoup(response.text, 'lxml')

    movie_link = soup.find('a',
                           class_="c-pageSiteSearch-results-item")

    # If we found a link, proceed to fetch the movie's page
    if movie_link:
        movie_url = "https://www.metacritic.com" + movie_link['href']
        print(movie_link['href'][7:-1].replace('-', ' '))
        code1 = get_phonetic_code(movie_link['href'][7:-1].replace('-', ' '))
        print(movie_title)
        code2 = get_phonetic_code(movie_title)
        print(fuzz.ratio(code1, code2))
        if fuzz.ratio(code1, code2) >= 100:
            response = requests.get(movie_url, headers=headers)
            if response.status_code == 200:
                driver = webdriver.Chrome(options=options)
                driver.get(movie_url)

                try:
                    element = driver.find_element("xpath", "//span[text()='Read More']")
                    driver.execute_script("arguments[0].click();", element)
                    time.sleep(1)
                except NoSuchElementException:
                    print("Did not find the 'Read More' button.")
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                driver.close()
                #soup = BeautifulSoup(response.text, 'lxml')


                score = soup.find('div',
                                       class_="c-siteReviewScore").text

                summary = soup.find('span',
                                       class_="c-productDetails_description g-text-xsmall").text

                genres = soup.find('ul',
                                       class_="c-genreList u-flexbox g-inner-spacing-top-medium").text


                genres = list(genres.split())

                return score, summary, genres, ""

            else:
                return "", "", "", "Failed to fetch movie page."
        else:
            return "", "", "", "Failed to find exach match: "+movie_link['href']
    else:
        return "", "", "", "Movie not found"
    #else:
    #    return "Failed to fetch search results."



title_df = pd.read_hdf('causal_review_df_new.h5')

if not os.path.exists("title_summary_genres_score.h5"):
    title_summary_genres_score_df = pd.DataFrame(columns=['title', 'meta_summary', 'meta_genres', 'meta_score'])
    title_summary_genres_score_df.to_hdf("title_summary_genres_score.h5", mode='w', key='df')


title_summary_genres_score_df = pd.read_hdf('title_summary_genres_score.h5')

for title in title_df['movie_title'].explode().unique():
    try:
        if title not in title_summary_genres_score_df['title'].values:
            movie_title = title
            # Simulated function to get metadata (replace with your actual function)
            meta_score, summary, genres, failure_comment = get_metacritic_info(movie_title)
            print(movie_title, summary, genres, meta_score, failure_comment)

            # Create a new row as a dictionary
            new_row = {'title': movie_title,
                       'meta_summary': summary,
                       'meta_genres': genres,
                       'meta_score': meta_score}

            # Append the new row to the DataFrame
            title_summary_genres_score_df = title_summary_genres_score_df._append(new_row, ignore_index=True)

        else:
            print(title, 'already in hdf.')

        # Store the updated DataFrame back into the HDF5 file after each successful addition
        title_summary_genres_score_df.to_hdf("title_summary_genres_score.h5", mode='a', key='df')

    except Exception as e:
        print(f"Error processing {title}: {e}")
        # Optionally, break or continue based on the error handling logic you prefer
        break

    # It's a good practice to also save outside the loop, to catch any changes made during the last iteration
title_summary_genres_score_df.to_hdf("title_summary_genres_score.h5", mode='w', key='df')