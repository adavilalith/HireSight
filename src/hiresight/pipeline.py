import os
import asyncio
from hiresight.db.postgres_client import PostgresClient
from hiresight.processors.job_parser import JobParser

async def run_silver_pipeline():
    # Load DB and Parser
    db = PostgresClient(os.getenv("POSTGRES_URL"))
    parser = JobParser()
    
    # 1. Fetch jobs (Bronze Layer)
    pending_jobs = db.get_unparsed_jobs(limit=10)
    
    if not pending_jobs:
        print("No pending jobs to parse.")
        return

    print(f"Starting Silver Pipeline: Processing {len(pending_jobs)} jobs...")

    for db_id, markdown in pending_jobs:
        try:
            # 2. Run Parallel Extraction (Silver Layer)
            # You MUST 'await' because JobParser.parse is now async
            result = await parser.parse(markdown)
            
            # 3. Save to the Silver Table (jobs_parsed)
            # result is a JobExtraction Pydantic object
            db.save_parsed_job(db_id, result)
            
            print(f"✅ Successfully parsed: {result.role} (Seniority: {result.seniority})")
            
        except Exception as e:
            # This catches validation errors or Groq API failures
            print(f"❌ Failed to parse job ID {db_id}: {str(e)}")
            # Optional: db.mark_as_failed(db_id) 

    db.close()

if __name__ == "__main__":
    # This is the entry point that kicks off the async event loop
    asyncio.run(run_silver_pipeline())