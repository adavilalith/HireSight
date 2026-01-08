import pytest
from hiresight.collectors.job_crawler import JobCrawler

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_crawl_integration():
    """Verify that Crawl4AI can actually hit a live site and return data."""
    crawler = JobCrawler()
    test_url = "https://example.com"
    
    description = await crawler.crawl_job_description(test_url)
    
    assert isinstance(description, str)
    assert len(description) > 0
    # Example.com markdown usually contains 'Example Domain'
    assert "Example Domain" in description