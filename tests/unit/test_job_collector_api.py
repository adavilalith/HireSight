import pytest
from unittest.mock import patch, MagicMock
from hiresight.collectors.job_collector import JobCollector

@pytest.fixture
def collector():
    with patch.dict("os.environ", {"SERPAPI_KEY": "fake_test_key"}):
        return JobCollector()
@pytest.mark.unit
def test_query_construction(collector):
    """Verify that experience levels change the search query correctly"""
    with patch("hiresight.collectors.job_collector.GoogleSearch") as mock_search:
        # Mock the return value of get_dict()
        mock_search.return_value.get_dict.return_value = {"jobs_results": []}
        
        collector.fetch_jobs(role="Data Analyst", location="Austin", experience_level="entry")
        
        # Check if "entry level" was actually added to the query sent to SerpApi
        args, _ = mock_search.call_args
        assert "entry level" in args[0]["q"]
@pytest.mark.unit
def test_fetch_jobs_returns_list(collector):
    """Verify the collector returns a list even if API returns data"""
    mock_data = {"jobs_results": [{"title": "Software Engineer", "company": "Google"}]}
    
    with patch("hiresight.collectors.job_collector.GoogleSearch") as mock_search:
        mock_search.return_value.get_dict.return_value = mock_data
        
        results = collector.fetch_jobs(role="DevOps", location="Remote")
        
        assert len(results) == 1
        assert results[0]["title"] == "Software Engineer"