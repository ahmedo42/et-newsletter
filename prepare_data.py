import json
from scraping import fetch_top_tmdb_content
from dotenv import load_dotenv
import os

load_dotenv(override=True)

TOP_K = int(os.environ.get("TOP_K"))
TIME_WINDOW = int(os.environ.get("TIME_WINDOW"))

movie_data = fetch_top_tmdb_content("movie", TOP_K, TIME_WINDOW)
shows_data = fetch_top_tmdb_content("tv", TOP_K, TIME_WINDOW)


with open("movies_data.json", "w", encoding="utf-8") as f:
        json.dump(movie_data, f, indent=4)

with open("shows_data.json", "w", encoding="utf-8") as f:
        json.dump(shows_data, f, indent=4)


