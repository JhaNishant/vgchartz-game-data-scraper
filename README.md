# vgchartz-game-data-scraper

A Python project to scrape game data from VGChartz for multiple genres.  
The script automatically retrieves available genres from the site, calculates the total number of results and pages (using 200 results per page), and scrapes game data including:

- **Console**
- **Game Name**
- **Publisher**
- **Total Shipped**
- **Total Sales**
- **Release Date**
- **Last Update**
- **Genre**

The data is saved to an Excel file (`vgchartz_games.xlsx`) or appended to it if the file already exists.

## Features

- **Automatic Genre Extraction:** Scrapes the available genres directly from the VGChartz search form.
- **Dynamic Pagination:** Calculates total pages based on the number of results (e.g., "Results: (8,872)").
- **Data Cleaning:** Removes unwanted text from game names and extracts console names from image alt attributes.
- **Concurrency:** Uses a thread pool to speed up scraping while handling rate limits (HTTP 429).
- **Excel Output:** Saves scraped data into an Excel file, appending new data if the file already exists.

## Requirements

- Python 3.12+
- Dependencies listed in [requirements.txt](requirements.txt)

Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

Run the scraper with:

```bash
python game_data.py
```

The script will scrape the VGChartz website and output the results to `vgchartz_games.xlsx`.

## License

This project is licensed under the MIT License.
