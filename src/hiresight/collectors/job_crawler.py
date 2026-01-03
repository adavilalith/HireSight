import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class JobCrawler:
    def __init__(self):
        # BrowserConfig handles global settings like headless mode and window size
        self.browser_config = BrowserConfig(
            headless=True, 
            verbose=True,
            # Helps bypass basic bot detection
            user_agent_mode="random" 
        )
        
        # CrawlerRunConfig handles per-page logic like Magic Mode
        self.run_config = CrawlerRunConfig(
            magic=True,                 # The "Magic" button for banners/popups
            remove_overlay_elements=True, # Forcefully strip blocking UI elements
            cache_mode=CacheMode.BYPASS, # Ensure we get fresh data
            page_timeout=60000          # 60s timeout for heavy job boards
        )

    async def crawl_job_description(self, url: str) -> str:
        """Visits a URL using Magic Mode to bypass popups."""
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            # We pass the run_config here
            result = await crawler.arun(
                url=url, 
                config=self.run_config
            )
            
            if result.success:
                # 'fit_markdown' is often cleaner than 'markdown' for job ads
                # as it focuses on the primary content area.
                return result.markdown.fit_markdown or result.markdown.raw_markdown
            else:
                print(f"❌ Failed to crawl {url}: {result.error_message}")
                return ""

# Usage
if __name__ == "__main__":
    crawler = JobCrawler()
    description = asyncio.run(crawler.crawl_job_description("https://example-job-board.com/job/123"))
    print(description)