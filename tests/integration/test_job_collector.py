import pytest
import os
from hiresight.collectors.job_collector import JobCollector

@pytest.mark.skipif(
    not os.getenv("SERPAPI_KEY"), 
    reason="SERPAPI_KEY not found in environment"
)
@pytest.mark.integration
def test_fetch_jobs_real_api():
    """Integration test: Hits the real SerpApi endpoint"""
    collector = JobCollector()
    
    # We use a very specific query to limit results and save credits
    results = collector.fetch_jobs(
        role="Data Analyst", 
        location="Hyderabad, Telangana, India",
        max_pages=1
    )
    
    # Assertions for real data
    assert isinstance(results, list)
    if len(results) > 0:
        assert "title" in results[0]
        assert "company_name" in results[0]
        print(f"\nSuccessfully fetched {len(results)} real jobs.")