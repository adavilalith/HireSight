import os
from typing import List, Dict, Any
from serpapi import GoogleSearch
from pydantic_settings import BaseSettings

class CollectorConfig(BaseSettings):
    """Loads API keys from .env automatically using pydantic"""
    serpapi_key: str = os.getenv("SERPAPI_KEY", "")
    print(serpapi_key)

class JobCollector:
    def __init__(self):
        self.config = CollectorConfig()
        if not self.config.serpapi_key:
            raise ValueError("SERPAPI_KEY not found in environment.")

    def fetch_jobs(
        self, 
        role: str, 
        location: str, 
        experience_level: str = "experienced", 
        max_pages: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Fetches job listings using SerpApi Google Jobs engine.
        experience_level: 'entry' or 'experienced'
        """
        
        # Keyword injection for experience filtering
        experience_keyword = "entry level" if experience_level.lower() == "entry" else "senior"
        query = f"{role} {experience_keyword}"
        
        all_jobs = []
        next_page_token = None

        for page in range(max_pages):
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": location,
                "hl": "en",
                "gl": "us",
                "api_key": self.config.serpapi_key
            }

            # Handle pagination
            if next_page_token:
                params["next_page_token"] = next_page_token

            search = GoogleSearch(params)
            results = search.get_dict()

            # Check for errors
            if "error" in results:
                print(f"Error fetching page {page}: {results['error']}")
                break

            jobs = results.get("jobs_results", [])
            all_jobs.extend(jobs)

            # Get token for next page
            next_page_token = results.get("serpapi_pagination", {}).get("next_page_token")
            if not next_page_token:
                break

        return all_jobs
