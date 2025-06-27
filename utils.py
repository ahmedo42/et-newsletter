import datetime
import requests
import time
from typing import List, Dict
import json

def get_time_window(time_window: int) -> tuple[str, str]:
    end = datetime.date.today()
    start = end - datetime.timedelta(days=time_window)
    return start.isoformat(), end.isoformat()


def get_subscribers(SENDGRID_API_KEY: str, LIST_ID: str, max_wait_time: int = 300) -> List[Dict[str, str]]:
    export_url = "https://api.sendgrid.com/v3/marketing/contacts/exports"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    export_payload = {
        "list_ids": [LIST_ID],
        "file_type": "json" 
    }

    try:
        response = requests.post(export_url, headers=headers, json=export_payload)
        response.raise_for_status()
        job_id = response.json().get("id")

        if not job_id:
            print("Failed to initiate export or get job ID.")
            return []

        print(f"Export initiated. Job ID: {job_id}")

        status_url = f"{export_url}/{job_id}"
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(status_url, headers=headers)
            status_response.raise_for_status()
            status_data = status_response.json()
            status = status_data.get("status")

            print(f"Export status: {status}...")

            if status == "ready":
                download_urls = status_data.get("urls", [])
                break
            elif status == "failed":
                print("Export failed.")
                return []
            
            time.sleep(5)
        else:
            print("Export timed out.")
            return []

        contacts = []
        for url in download_urls:
            print(f"Downloading from: {url}")
            
            download_response = requests.get(url)  # No headers for S3
            download_response.raise_for_status()
            
            # Parse NDJSON (each line is a separate JSON object)
            for line in download_response.text.strip().split('\n'):
                if line.strip():  # Skip empty lines
                    contact = json.loads(line)
                    contacts.append(contact["email"])
                        
            return contacts
        
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return []