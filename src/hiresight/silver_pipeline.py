import os
import asyncio
from hiresight.db.postgres_client import PostgresClient
from hiresight.processors.job_parser import JobParser

async def run_silver_pipeline():
    db = PostgresClient(os.getenv("POSTGRES_URL"))
    parser = JobParser()
    
    print("🚀 Silver Pipeline Worker Started...")

    while True:
        # 1. Claim a job (FOR UPDATE SKIP LOCKED)
        db_id, markdown, cursor = db.get_job_with_lock()
        
        if not db_id:
            exit(0) # No more jobs to process, exit the worker

        try:
            print(f"🔄 Processing Job ID: {db_id}...")
            
            # 2. LLM Extraction
            result = await parser.parse(markdown)
            
            # 3. Atomic Save & Status Update
            db.finalize_job(cursor, db_id, result)
            print(f"✅ Finished: {result.role}")
        except Exception as e:
            print(f"❌ Error on Job {db_id}: {e}")
            # If we rollback, status returns to 'pending' unless we explicitly
            # change it to 'failed' in a new transaction.
            db.conn.rollback()
            cursor.close()
        # 4. Staggered delay to stay under Groq free tier limits
        await asyncio.sleep(180) # 3 minutes delay

if __name__ == "__main__":
    # This is the entry point that kicks off the async event loop
    asyncio.run(run_silver_pipeline())