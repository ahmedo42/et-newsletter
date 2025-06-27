import logging
import requests
from bs4 import BeautifulSoup
import re
import os 

from utils import get_time_window 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")



def fetch_detailed_info(content_id: str, content_type: str, title: str) -> dict:
    logging.info(f"Fetching detailed info for {title}")
    
    # Get main details
    details_url = f"{BASE_URL}/{content_type}/{content_id}"
    details_resp = requests.get(details_url, params={"api_key": TMDB_API_KEY})
    details_resp.raise_for_status()
    details_data = details_resp.json()

    # Get credits
    credits_url = f"{BASE_URL}/{content_type}/{content_id}/credits"
    credits_resp = requests.get(credits_url, params={"api_key": TMDB_API_KEY})
    credits_resp.raise_for_status()
    credits_data = credits_resp.json()

    # Get IMDb ID (especially important for TV)
    if content_type == "tv":
        external_ids_url = f"{BASE_URL}/tv/{content_id}/external_ids"
    else:
        external_ids_url = f"{BASE_URL}/movie/{content_id}/external_ids"

    external_ids_resp = requests.get(external_ids_url, params={"api_key": TMDB_API_KEY})
    external_ids_resp.raise_for_status()
    external_ids = external_ids_resp.json()
    imdb_id = external_ids.get("imdb_id")

    # Extract data
    genres = [g['name'] for g in details_data.get("genres", [])]
    overview = details_data.get("overview")
    cast = [member['name'] for member in credits_data.get("cast", [])[:4]]
    crew = credits_data.get("crew", [])

    directors = [member['name'] for member in crew if member.get("job") == "Director"]
    writers = [member['name'] for member in crew if member.get("job") in ["Writer", "Screenplay", "Author", "Writing", "Novel"]]

    if content_type == "movie":
        return {
            "genres": genres,
            "cast": cast,
            "directors": directors,
            "writers": writers,
            "overview": overview,
            "imdb_url": f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None
        }
    else:
        # Use created_by field if available, fallback to crew for creators
        creators = [member['name'] for member in details_data.get("created_by", [])]
        if not creators:
            creators = list({member['name'] for member in crew if member.get("job") == "Creator"})

        return {
            "genres": genres,
            "cast": cast,
            "creators": creators,
            "overview": overview,
            "imdb_url": f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None
        }

def fetch_top_tmdb_content(content_type: str, limit: int, time_window: int) -> list:
    start_date, end_date = get_time_window(time_window)
    url = f"{BASE_URL}/discover/{content_type}"
    params = {
        "api_key": TMDB_API_KEY,
        "sort_by": "vote_count.desc",
        "primary_release_date.gte" if content_type == "movie" else "first_air_date.gte": start_date,
        "primary_release_date.lte" if content_type == "movie" else "first_air_date.lte": end_date,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json().get("results", [])[:limit]

    results = []
    for item in data:
        content_id = item.get("id")
        title = item.get("title") or item.get("name")
        release_date = item.get("release_date") or item.get("first_air_date")
        poster_path = item.get("poster_path")
        metacrtic_score = get_metacritic_score(title, content_type, release_date[:4])
        rotten_tomatoes_scores = get_rotten_tomatoes_scores(title, 'm' if content_type == "movie" else 'tv', release_date[:4])
        if not metacrtic_score and not rotten_tomatoes_scores['critic_score']:
            continue

        details = fetch_detailed_info(content_id, content_type, title)

        results.append({
            "title": title,
            "id": content_id,
            "release_date": release_date,
            "poster_path": poster_path,
            "metacritic_score": metacrtic_score,
            "rotten_tomatoes_scores": rotten_tomatoes_scores,
            **details
        })

    return results


def get_metacritic_score(movie_title: str, content_type: str, release_year: str) -> int | None:
    logging.info(f"Fetching Rotten Tomatoes scores for '{movie_title}'")
    base_url = f"https://www.metacritic.com/{content_type}/"

    # Slugify the movie title
    # Convert to lowercase, replace spaces with hyphens, remove non-alphanumeric characters
    # Example: "Spider-Man: Into the Spider-Verse" -> "spider-man-into-the-spider-verse"
    movie_title  = movie_title.replace("'", "").replace(".","")
    slugified_title = re.sub(r'[^a-z0-9\s-]', '', movie_title.lower()).replace(' ', '-')
    movie_page_url = f"{base_url}{slugified_title}-{release_year}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    if requests.head(movie_page_url,headers=headers).status_code != 200:
        movie_page_url = f"{base_url}{slugified_title}/"



    try:
        movie_response = requests.get(movie_page_url,headers=headers, timeout=10)
        movie_response.raise_for_status()
        movie_soup = BeautifulSoup(movie_response.text, 'html.parser')

        score_div = movie_soup.find(
            'div',
            class_=lambda x: x and 'c-siteReviewScore' in x,
            title=lambda x: x and x.startswith('Metascore')
        )

        score_text = None
        if score_div:
            score_span = score_div.find('span')
            if score_span:
                score_text = score_span.get_text(strip=True)
                logging.info(f"Found metascore using new selector: {score_text}")

        if score_text is None:
            logging.info(f"Metascore element not found for '{movie_title}' on its page using any selector.")
            return None

        try:
            score = int(score_text)
            return score
        except ValueError:
            logging.warning(f"Metacritic is TBD")
            return None

    except requests.exceptions.RequestException as e:
        logging.info(f"Network error fetching Metacritic score for '{movie_title}': {e}")
        return None
    except Exception as e:
        logging.info(f"An unexpected error occurred: {e}")
        return None


def get_rotten_tomatoes_scores(movie_title: str, content_type: str, release_year: str) -> dict:

    logging.info(f"Fetching Rotten Tomatoes scores for '{movie_title}'")
    movie_title  = movie_title.replace("'", "").replace(".","")
    movie_slug = re.sub(r'[^a-z0-9]+', '_', movie_title.lower()).strip('_')
    url = f"https://www.rottentomatoes.com/{content_type}/{movie_slug}_{release_year}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    if requests.head(url,headers=headers).status_code != 200:
        url = f"https://www.rottentomatoes.com/{content_type}/{movie_slug}"



    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        logging.info(f"Error fetching URL {url}: {e}")
        return {
            'critic_score': None,
            'audience_score': None
        }

    soup = BeautifulSoup(response.text, 'html.parser')


    # Find the critic score (Tomatometer)
    critic_score_tag = soup.find('rt-text', slot='criticsScore')
    if critic_score_tag:
        score_text = critic_score_tag.get_text(strip=True)
        # Extract only digits and convert to int
        match = re.search(r'(\d+)%', score_text)
        if match:
            critic_score = match.group(1)

    # Find the audience score
    audience_score_tag = soup.find('rt-text', slot='audienceScore')
    if audience_score_tag:
        score_text = audience_score_tag.get_text(strip=True)
        # Extract only digits and convert to int
        match = re.search(r'(\d+)%', score_text)
        if match:
            audience_score = match.group(1)
    
    try : 
        critic_score = int(critic_score)
    except : 
        critic_score = None

    try:
        audience_score = int(audience_score)
    except : 
        audience_score = None

    return {
        'critic_score': critic_score,
        'audience_score': audience_score
    }