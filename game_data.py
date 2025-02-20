#!/usr/bin/env python3
"""
vgchartz-game-data-scraper

A Python script to scrape VGChartz game data for multiple genres.
It automatically retrieves available genres, determines the total number of results
(for each genre), calculates the total pages (using 200 results per page), and scrapes game data,
including console, game name, publisher, total shipped, total sales, release date, and last update.
The results are saved to an Excel file (vgchartz_games.xlsx) or appended if the file already exists.

Usage:
    python game_data.py

Dependencies:
    - requests
    - beautifulsoup4
    - pandas
    - openpyxl

Install dependencies via:
    pip install -r requirements.txt
"""

import os
import re
import math
import time
import random
import requests
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd
import concurrent.futures

RESULTS_PER_PAGE = 200  # Using 200 results per page

def fetch_url(url, max_retries=5):
    """
    Fetch the URL with retries and backoff if a 429 (Too Many Requests) is encountered.
    Returns the HTML text if successful, otherwise None.
    """
    for attempt in range(1, max_retries + 1):
        time.sleep(random.uniform(1, 3))
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.text
        elif resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After", 30)
            print(f"[fetch_url] 429 received. Attempt {attempt}/{max_retries}. Retrying in {retry_after} seconds...")
            time.sleep(int(retry_after))
        else:
            print(f"[fetch_url] HTTP {resp.status_code} on attempt {attempt}.")
            break
    return None

def get_genres():
    """
    Retrieves available genres from the VGChartz search form.
    Returns a list of genre values.
    """
    url = "https://www.vgchartz.com/games/games.php"
    html = fetch_url(url)
    genres = []
    if html:
        soup = BeautifulSoup(html, "html.parser")
        select = soup.find("select", attrs={"name": "genre"})
        if select:
            options = select.find_all("option")
            for option in options:
                value = option.get("value", "").strip()
                if value:  # Skip the blank first option
                    genres.append(value)
    return genres

def get_total_results(genre):
    """
    For a given genre, fetches the first page and extracts the total number of results.
    Returns an integer representing the total results, or None if not found.
    """
    encoded_genre = urllib.parse.quote_plus(genre)
    base_url = (
        "https://www.vgchartz.com/games/games.php?"
        "name=&keyword=&console=&region=All&developer=&publisher=&goty_year=&genre={}"
        "&boxart=Both&banner=Both&ownership=Both&showmultiplat=No&results={}&order=Popular"
        "&showtotalsales=0&showtotalsales=1&showpublisher=0&showpublisher=1&showvgchartzscore=0"
        "&shownasales=0&showdeveloper=0&showcriticscore=0&showpalsales=0&showreleasedate=0"
        "&showreleasedate=1&showuserscore=0&showjapansales=0&showlastupdate=0&showlastupdate=1"
        "&showothersales=0&showshipped=0&showshipped=1"
    ).format(encoded_genre, RESULTS_PER_PAGE) + "&page=1"
    html = fetch_url(base_url)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        th = soup.find("th", text=re.compile(r"Results:\s*\([\d,]+\)"))
        if th:
            text = th.get_text(strip=True)
            match = re.search(r"Results:\s*\(([\d,]+)\)", text)
            if match:
                total_str = match.group(1).replace(",", "")
                try:
                    return int(total_str)
                except ValueError:
                    pass
    return None

def scrape_page(url, genre):
    """
    Scrapes a single page from the VGChartz results.
    Returns a list of rows with columns:
      [Console, Game, Publisher, Total Shipped, Total Sales, Release Date, Last Update, Genre]
    """
    rows_data = []
    html = fetch_url(url)
    if not html:
        return rows_data

    soup = BeautifulSoup(html, "html.parser")
    header_th = soup.find("th", string=lambda text: text and "Pos" in text)
    if not header_th:
        return rows_data

    data_table = header_th.find_parent("table")
    if not data_table:
        return rows_data

    table_rows = data_table.find_all("tr")
    for row in table_rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 9:
            continue

        game_cell = cells[2]
        game_text = game_cell.get_text(strip=True)
        game_name = game_text.replace("Read the review", "").strip()

        console = None
        for c_idx in [2, 3]:
            if c_idx < len(cells):
                img = cells[c_idx].find("img", alt=lambda x: x and x != "Boxart Missing")
                if img:
                    console = img.get("alt", "").strip()
                    break
        if not console:
            console = "Unknown"

        publisher = cells[4].get_text(strip=True)
        total_shipped = cells[5].get_text(strip=True)
        total_sales = cells[6].get_text(strip=True)
        release_date = cells[7].get_text(strip=True)
        last_update = cells[8].get_text(strip=True)

        rows_data.append([
            console,
            game_name,
            publisher,
            total_shipped,
            total_sales,
            release_date,
            last_update,
            genre
        ])
    return rows_data

def main():
    excel_file = "vgchartz_games.xlsx"
    max_workers = 2  # Adjust to avoid 429 errors

    genres = get_genres()
    if not genres:
        print("Could not retrieve any genres. Exiting.")
        return

    print("Found genres:")
    for g in genres:
        print(" -", g)

    all_data = []

    for genre in genres:
        print(f"\nProcessing genre: {genre}")
        total = get_total_results(genre)
        if total is None:
            print(f"  Could not determine total results for genre {genre}. Skipping.")
            continue

        total_pages = math.ceil(total / RESULTS_PER_PAGE)
        print(f"  Total results: {total} => {total_pages} pages at {RESULTS_PER_PAGE} results per page.")

        encoded_genre = urllib.parse.quote_plus(genre)
        base_url = (
            "https://www.vgchartz.com/games/games.php?"
            "name=&keyword=&console=&region=All&developer=&publisher=&goty_year=&genre={}"
            "&boxart=Both&banner=Both&ownership=Both&showmultiplat=No&results={}&order=Popular"
            "&showtotalsales=0&showtotalsales=1&showpublisher=0&showpublisher=1&showvgchartzscore=0"
            "&shownasales=0&showdeveloper=0&showcriticscore=0&showpalsales=0&showreleasedate=0"
            "&showreleasedate=1&showuserscore=0&showjapansales=0&showlastupdate=0&showlastupdate=1"
            "&showothersales=0&showshipped=0&showshipped=1"
        ).format(encoded_genre, RESULTS_PER_PAGE)

        genre_data = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {}
            for page in range(1, total_pages + 1):
                url = base_url + f"&page={page}"
                future = executor.submit(scrape_page, url, genre)
                future_to_page[future] = page

            for future in concurrent.futures.as_completed(future_to_page):
                page_number = future_to_page[future]
                try:
                    page_data = future.result()
                    genre_data.extend(page_data)
                    print(f"  Genre {genre} - Page {page_number} done. Rows found: {len(page_data)}")
                except Exception as e:
                    print(f"  Error scraping genre {genre} page {page_number}: {e}")

        print(f"Completed genre {genre}: {len(genre_data)} rows collected.")
        all_data.extend(genre_data)

    df_current = pd.DataFrame(all_data, columns=[
        "Console", "Game", "Publisher", "Total Shipped",
        "Total Sales", "Release Date", "Last Update", "Genre"
    ])

    if os.path.exists(excel_file):
        df_existing = pd.read_excel(excel_file)
        df_combined = pd.concat([df_existing, df_current], ignore_index=True)
        df_combined.to_excel(excel_file, index=False)
        print(f"\nAppended data to {excel_file}. Total records now: {len(df_combined)}")
    else:
        df_current.to_excel(excel_file, index=False)
        print(f"\nCreated new file {excel_file} with {len(df_current)} records.")

if __name__ == "__main__":
    main()
