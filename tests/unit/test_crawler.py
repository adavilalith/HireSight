import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from hiresight.collectors.job_crawler import JobCrawler

@pytest.mark.unit
@pytest.mark.asyncio
async def test_crawl_job_description_success_prefers_fit_markdown():
    """Test that we return fit_markdown if it exists."""
    crawler = JobCrawler()
    
    # Setup Mocks
    mock_result = MagicMock()
    mock_result.success = True
    # Crawl4AI results use a nested object for markdown
    mock_result.markdown = MagicMock()
    mock_result.markdown.fit_markdown = "Cleaned Content"
    mock_result.markdown.raw_markdown = "Messy Content"
    
    with patch("hiresight.collectors.job_crawler.AsyncWebCrawler") as MockCrawler:
        # Configure the context manager to return an object with 'arun'
        instance = MockCrawler.return_value.__aenter__.return_value
        instance.arun = AsyncMock(return_value=mock_result)
        
        description = await crawler.crawl_job_description("https://fake-url.com")
        
        assert description == "Cleaned Content"
        instance.arun.assert_called_once()

@pytest.mark.unit
@pytest.mark.asyncio
async def test_crawl_job_description_failure_returns_empty_string():
    """Test error handling when crawl fails."""
    crawler = JobCrawler()
    
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error_message = "404 Not Found"
    
    with patch("hiresight.collectors.job_crawler.AsyncWebCrawler") as MockCrawler:
        instance = MockCrawler.return_value.__aenter__.return_value
        instance.arun = AsyncMock(return_value=mock_result)
        
        description = await crawler.crawl_job_description("https://broken-url.com")
        
        assert description == ""