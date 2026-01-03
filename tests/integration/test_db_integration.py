import pytest
import os
from hiresight.collectors.job_collector import JobCollector
from hiresight.db.postgres_client import PostgresClient

@pytest.mark.integration
def test_collector_to_postgres_flow(db_client):
    """
    Test the full flow: 
    1. Fetch real data from SerpApi
    2. Save it to the Postgres test database
    3. Verify data integrity
    """
    # 1. Arrange
    collector = JobCollector()
    role = "Data Analyst"
    location = "Hyderabad, Telangana, India"    
    # 2. Act
    # Fetch just 1 page to minimize API credit usage
    jobs = collector.fetch_jobs(role=role, location=location, max_pages=1)
    
    if not jobs:
        pytest.skip("No jobs returned from API, cannot test DB integration")
        
    db_client.save_jobs(jobs, role, location)
    
    # 3. Assert
    with db_client.conn.cursor() as cur:
        cur.execute("SELECT raw_json FROM jobs_raw WHERE role_searched = %s LIMIT 1;", (role,))
        result = cur.fetchone()
        
    assert result is not None
    raw_data = result[0]
    assert "title" in raw_data
    assert "company_name" in raw_data
    print(f"\nIntegration Success: Saved {len(jobs)} real jobs to Postgres.")