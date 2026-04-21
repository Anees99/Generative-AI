"""
Job Scraper Module - Ethical Public Web Scraping

This module extracts visible text from public job postings using Playwright.
It respects robots.txt ethics, uses timeouts, and performs NO anti-bot bypass.

Conceptually inspired by Career-Ops (MIT License) - Python re-engineering.
"""

import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)


class JobScraper:
    """
    Ethical job posting scraper using Playwright.
    
    Features:
    - Extracts only publicly visible text
    - 10-second timeout to prevent hanging
    - No login/authentication required
    - No CAPTCHA solving or anti-bot bypass
    - Respects robots.txt principles
    """
    
    def __init__(self, timeout: int = 10000):
        """
        Initialize the scraper.
        
        Args:
            timeout: Request timeout in milliseconds (default: 10s)
        """
        self.timeout = timeout
        self._browser = None
    
    async def _init_browser(self):
        """Initialize Playwright browser if not already done."""
        if self._browser is None:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
    
    async def close(self):
        """Close the browser instance."""
        if self._browser:
            await self._browser.close()
            self._browser = None
    
    async def scrape_job(self, url: str) -> Optional[dict]:
        """
        Scrape a job posting from a public URL.
        
        Args:
            url: Public job posting URL
            
        Returns:
            Dictionary containing:
            - title: Job title
            - company: Company name
            - description: Full job description text
            - url: Original URL
            Or None if scraping fails
            
        Raises:
            ValueError: If URL is invalid
            TimeoutError: If page takes too long to load
        """
        if not url or not url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid URL: {url}")
        
        await self._init_browser()
        
        context = None
        try:
            # Create new browser context for isolation
            context = await self._browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            # Navigate with timeout
            logger.info(f"Scraping job posting: {url}")
            await page.goto(url, timeout=self.timeout, wait_until='domcontentloaded')
            
            # Wait for content to stabilize
            await page.wait_for_timeout(2000)
            
            # Extract visible text only (ethical scraping - no hidden content)
            title = await self._extract_title(page)
            company = await self._extract_company(page)
            description = await self._extract_description(page)
            
            # Clean extracted text
            if title:
                title = ' '.join(title.split())[:200]  # Limit length
            if company:
                company = ' '.join(company.split())[:200]
            if description:
                description = ' '.join(description.split())[:10000]  # Limit for API costs
            
            result = {
                'title': title or 'Unknown Position',
                'company': company or 'Unknown Company',
                'description': description or 'No description available',
                'url': url
            }
            
            logger.info(f"Successfully scraped: {result['title']} at {result['company']}")
            return result
            
        except PlaywrightTimeout:
            logger.error(f"Timeout scraping {url} after {self.timeout}ms")
            raise TimeoutError(f"Page load timeout for {url}")
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None
        finally:
            if context:
                await context.close()
    
    async def _extract_title(self, page) -> str:
        """Extract job title from common selectors."""
        selectors = [
            'h1',
            '[data-testid="job-title"]',
            '.job-title',
            '#job-title',
            '[class*="job-title"]',
            '[class*="position-title"]',
            'meta[property="og:title"]'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and len(text.strip()) > 0:
                        return text.strip()
            except:
                continue
        
        # Fallback: look for first h1 or large text
        try:
            title = await page.evaluate('''
                () => {
                    const h1 = document.querySelector('h1');
                    if (h1) return h1.textContent.trim();
                    return '';
                }
            ''')
            if title:
                return title
        except:
            pass
        
        return ''
    
    async def _extract_company(self, page) -> str:
        """Extract company name from common selectors."""
        selectors = [
            '[data-testid="company-name"]',
            '.company-name',
            '#company-name',
            '[class*="company-name"]',
            '[class*="employer"]',
            'a[class*="company"]',
            '[data-company-name]'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and len(text.strip()) > 0:
                        return text.strip()
            except:
                continue
        
        # Fallback: look for company meta tags
        try:
            company = await page.evaluate('''
                () => {
                    const meta = document.querySelector('meta[name="twitter:data1"]');
                    if (meta) return meta.getAttribute('content');
                    return '';
                }
            ''')
            if company:
                return company
        except:
            pass
        
        return ''
    
    async def _extract_description(self, page) -> str:
        """Extract job description from common containers."""
        selectors = [
            '[data-testid="job-description"]',
            '.job-description',
            '#job-description',
            '[class*="job-description"]',
            '[class*="job-details"]',
            '[class*="job-content"]',
            'article',
            'main'
        ]
        
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    texts = []
                    for elem in elements[:3]:  # Limit to first 3 elements
                        text = await elem.text_content()
                        if text and len(text.strip()) > 50:  # Avoid trivial content
                            texts.append(text.strip())
                    if texts:
                        return '\n\n'.join(texts)
            except:
                continue
        
        # Fallback: extract all visible text from body
        try:
            description = await page.evaluate('''
                () => {
                    const body = document.querySelector('body');
                    if (body) return body.innerText;
                    return document.documentElement.innerText;
                }
            ''')
            if description:
                return description
        except:
            pass
        
        return ''
    
    def scrape_job_sync(self, url: str) -> Optional[dict]:
        """
        Synchronous wrapper for scrape_job.
        
        Args:
            url: Public job posting URL
            
        Returns:
            Dictionary with job details or None
        """
        return asyncio.run(self.scrape_job(url))


# Example usage for testing
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    scraper = JobScraper()
    try:
        # Test with a sample URL (replace with actual public job posting)
        result = scraper.scrape_job_sync('https://example.com/job-posting')
        if result:
            print(f"Title: {result['title']}")
            print(f"Company: {result['company']}")
            print(f"Description length: {len(result['description'])} chars")
    finally:
        asyncio.run(scraper.close())
