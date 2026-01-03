import json
import os
import asyncio
from dotenv import load_dotenv
from hiresight.collectors.job_collector import JobCollector
from hiresight.db.postgres_client import PostgresClient
from hiresight.collectors.job_crawler import JobCrawler

load_dotenv()

async def run_pipeline():
    # --- PHASE 1: INGESTION ---
    # collector = JobCollector()
    db = PostgresClient(os.getenv("POSTGRES_URL"))
    
    role = "Data Analyst"
    location = "Hyderabad, Telangana, India"
    
    # print(f"🔍 [Phase 1] Collecting jobs for {role} in {location}...")
    # jobs = collector.fetch_jobs(role=role, location=location, max_pages=1)
    
    # if jobs:
    #     db.save_jobs(jobs, role, location)
    #     with open('data.json', 'w') as f:
    #             json.dump(jobs, f, indent=4)
    print("\nSKIPPING PHASE 1: INGESTION to save API tokens\n")

    # --- PHASE 2: CRAWLING ---
    print(f"🕷️ [Phase 2] Starting Crawl4AI for pending jobs...")
    crawler = JobCrawler()
    
    # Fetch id and URL for jobs where crawled = FALSE
    pending_jobs = db.get_pending_jobs(limit=5) 
    
    for id, url in pending_jobs:
        print(f"📝 Crawling: {url[:50]}...")
        markdown = await crawler.crawl_job_description(url)
        
        if markdown:
            # Update the DB with the full text and set crawled = TRUE
            db.update_job_description(id, markdown)
            print(f"✅ Saved description for {id}")
        else:
            print(f"⚠️ Skipping {id} due to crawl error.")

    db.close()
    print("🚀 Pipeline Finished!")

if __name__ == "__main__":
    # We use asyncio.run because the crawler is async
    asyncio.run(run_pipeline())