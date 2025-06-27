
# 🎬 ET Newsletter

I built this project to generate and send a curated newsletter featuring top-rated movies and TV shows to me and my friends. It uses the TMDB API to fetch content, scrapes Metacritic and Rotten Tomatoes for review scores, and uses SendGrid to distribute the formatted HTML newsletter.

## ✨ Features

- **Content Curation**: Fetches top movies and TV shows from TMDB based on a configurable time window and popularity.
- **Review Aggregation**: Scrapes Metacritic and Rotten Tomatoes to gather critic and audience scores for featured content.
- **Dynamic Newsletter Generation**: Generates a dynamic and responsive HTML newsletter using Jinja2 templates.
- **Email Compatibility**: Inlines CSS into the HTML to ensure consistent rendering across various email clients using `premailer`.
- **Email Distribution**: Sends the generated newsletter to a list of subscribers via SendGrid.
- **Test Mode**: Includes a convenient test mode for sending newsletters to a single recipient for review before a full send.

## 🚀 Getting Started

Follow these steps to set up and run the project.


### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/et-newsletter.git
    cd et-newsletter
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Create a `.env` file in the root directory of the project based on the provided `.env.example`.

```ini
# .env
TMDB_API_KEY=your_tmdb_api_key_here
TOP_K=5 # Number of top movies/shows to fetch
TIME_WINDOW=30 # Days back to consider for trending content
SENDGRID_API_KEY=your_sendgrid_api_key_here
LIST_ID=your_sendgrid_list_id_here # ID of your SendGrid contact list
FROM_EMAIL=newsletter@example.com # Sender email address
TEST_EMAIL_RECIPIENT=test@example.com # Email for testing purposes
UNSUBSCRIBE_GROUP_ID=your_sendgrid_unsubscribe_group_id # SendGrid unsubscribe group ID
