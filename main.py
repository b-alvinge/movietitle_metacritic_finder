import requests
from bs4 import BeautifulSoup
import pandas as pd
import Levenshtein
from selenium import webdriver
import time

from selenium.common import NoSuchElementException


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
        if Levenshtein.ratio(movie_link['href'][7:-1], search_query) >= 1:
            response = requests.get(movie_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')


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



title_script_df = pd.read_excel('title_script_output.xlsx')
title_script_summary_genres_score_df = pd.DataFrame()
for _, row in title_script_df.iterrows():
    movie_title = row['title']
    script = row['script']
    meta_score, summary, genres, failure_comment = get_metacritic_info(movie_title)
    print(movie_title, summary, genres, meta_score, failure_comment)
    new_row = {'title': movie_title,
               'script': script,
               'meta_summary': summary,
               'meta_genres': genres,
               'meta_score': meta_score}
    # append the new row to the DataFrame
    title_script_summary_genres_score_df = title_script_summary_genres_score_df._append(new_row, ignore_index=True)

title_script_summary_genres_score_df.to_excel("title_script_summary_genres_score_output3.xlsx", index=False)