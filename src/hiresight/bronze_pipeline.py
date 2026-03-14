import json
import os
import asyncio
from dotenv import load_dotenv
from hiresight.collectors.job_collector import JobCollector
from hiresight.db.postgres_client import PostgresClient
from hiresight.collectors.job_crawler import JobCrawler

load_dotenv()

async def run_bronze_pipeline(config_path="jobs_config.json"):
    # Load configuration
    if not os.path.exists(config_path):
        print(f"❌ Config file {config_path} not found.")
        return

    with open(config_path, 'r') as f:
        search_targets = json.load(f)

    # Initialize shared clients
    collector = JobCollector()
    db = PostgresClient(os.getenv("POSTGRES_URL"))
    crawler = JobCrawler()

    # --- PHASE 1: INGESTION LOOP ---
    for target in search_targets:
        role = target.get("role")
        location = target.get("location")
        
        print(f"\n[Phase 1] Collecting jobs for {role} in {location}...")
        try:
            jobs = collector.fetch_jobs(role=role, location=location, max_pages=5)
            if jobs:
                db.save_jobs(jobs, role, location)
        except Exception as e:
            print(f"⚠️ Failed to fetch {role}: {e}")

    # --- PHASE 2: CRAWLING ---
    print(f"[Phase 2] Multi-source Crawl for Hyderabad jobs...")
    crawler = JobCrawler()
    pending_jobs = db.get_pending_jobs(limit=5) 
    
    for db_id, apply_options in pending_jobs:
        successful_crawls = []
        # apply_options is a list of dicts: [{'title': '...', 'link': '...'}, ...]
        for option in apply_options:
            option = option
            url = option.get('link')
            source_name = option.get('title', 'Unknown Source')
            
            if len(successful_crawls) >= 3:
                break # Stop if we already have 3 sources
            print(f"📄 Trying {source_name}: {url[:40]}...")
            markdown = await crawler.crawl_job_description(url)
            
            if markdown and len(markdown) > 200: # Ensure it's not just a 'Cookie' page
                header = f"--- SOURCE: {source_name} ---\n"
                successful_crawls.append(header + markdown)
                print(f"Success from {source_name}")
            else:
                print(f"Failed or empty crawl for {source_name}. Skipping...")

        if successful_crawls:
            # Combine all successful results with a separator
            final_content = "\n\n".join(successful_crawls)
            db.update_job_description(db_id, final_content)
            print(f"🏁 Finished job {db_id} using {len(successful_crawls)} sources.")
        else:
            print(f"Could not crawl any links for job {db_id}.")

    db.close()
    print("Pipeline Finished!")

if __name__ == "__main__":
    # We use asyncio.run because the crawler is async
    asyncio.run(run_bronze_pipeline())