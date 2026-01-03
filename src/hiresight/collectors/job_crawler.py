import asyncio
from crawl4ai import AsyncWebCrawler

class JobCrawler:
    def __init__(self):
        # We can add custom headers or browser configs here later
        pass

    async def crawl_job_description(self, url: str) -> str:
        """Visits a URL and returns clean, markdown-formatted text."""
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(url=url)
            
            if result.success:
                # result.markdown is pre-cleaned text perfect for LLMs
                return result.markdown
            else:
                print(f"Failed to crawl {url}: {result.error_message}")
                return ""

# Simple test runner for this class
if __name__ == "__main__":
    crawler = JobCrawler()
    # Testing with a real URL (using Hyderabad-based job board if possible)
    sample_url = "https://www.google.com/about/careers/applications/jobs/results/" 
    description = asyncio.run(crawler.crawl_job_description(sample_url))
    print(description[:500]) # Print first 500 chars