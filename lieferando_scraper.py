"""
Lieferando.de Scraper using Playwright

This script scrapes restaurant information from lieferando.de including:
- Restaurant name
- Company name
- Reviews (count and text)
- Rating
- Email address (if available)

IMPORTANT LEGAL NOTICE:
- Review lieferando.de Terms of Service before using this scraper
- Respect robots.txt and rate limits
- This is for educational purposes only
- Do not use for commercial purposes without permission
"""

import asyncio
import json
import random
from typing import Dict, List, Optional
from playwright.async_api import async_playwright


class LieferandoScraper:
    def __init__(self, headless: bool = True, slow_mo: int = 1000):
        self.headless = headless
        self.slow_mo = slow_mo  # Slow down to avoid detection
        self.base_url = "https://www.lieferando.de"
        
    async def scrape_restaurant(self, restaurant_url: str) -> Optional[Dict]:
        """Scrape a single restaurant page"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            
            page = await context.new_page()
            
            try:
                # Navigate to restaurant page
                await page.goto(restaurant_url, wait_until="networkidle", timeout=30000)
                
                # Wait for content to load
                await page.wait_for_timeout(3000)
                
                # Extract restaurant name
                restaurant_name = await self._extract_restaurant_name(page)
                
                # Extract company name
                company_name = await self._extract_company_name(page)
                
                # Extract rating
                rating = await self._extract_rating(page)
                
                # Extract reviews
                reviews = await self._extract_reviews(page)
                
                # Extract email address
                email = await self._extract_email(page)
                
                result = {
                    "url": restaurant_url,
                    "restaurant_name": restaurant_name,
                    "company_name": company_name,
                    "rating": rating,
                    "reviews_count": len(reviews) if reviews else 0,
                    "reviews": reviews[:10] if reviews else [],  # Limit to first 10 reviews
                    "email": email,
                    "scraped_at": asyncio.get_event_loop().time()
                }
                
                return result
                
            except Exception as e:
                print(f"Error scraping {restaurant_url}: {str(e)}")
                return None
            finally:
                await browser.close()
    
    async def _extract_restaurant_name(self, page) -> Optional[str]:
        """Extract restaurant name"""
        selectors = [
            'h1[data-automation="restaurant-name"]',
            'h1.restaurant-name',
            '[data-automation="restaurant-header-title"]',
            'header h1',
            '.restaurant-info h1'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return await element.inner_text()
            except:
                continue
        
        return None
    
    async def _extract_company_name(self, page) -> Optional[str]:
        """Extract company/legal name"""
        # Look for legal information, imprint, or company details
        selectors = [
            '[data-automation="restaurant-imprint"]',
            '.imprint',
            '.legal-info',
            '[class*="imprint"]',
            '[class*="legal"]'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    # Try to extract company name from legal text
                    return text.strip()[:500]  # Limit length
            except:
                continue
        
        # Alternative: look for "Inhaber" or "Company" mentions
        try:
            content = await page.content()
            # Simple pattern matching for company info
            if "Inhaber" in content:
                # Extract surrounding text
                return "Found in page content (manual extraction needed)"
        except:
            pass
        
        return None
    
    async def _extract_rating(self, page) -> Optional[float]:
        """Extract restaurant rating"""
        selectors = [
            '[data-automation="restaurant-rating"]',
            '[data-automation="score-value"]',
            '.rating-value',
            '[class*="rating"] span',
            'span[class*="score"]'
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    # Extract numeric value
                    import re
                    match = re.search(r'(\d+[.,]?\d*)', text.replace(',', '.'))
                    if match:
                        return float(match.group(1).replace(',', '.'))
            except:
                continue
        
        return None
    
    async def _extract_reviews(self, page) -> List[Dict]:
        """Extract customer reviews"""
        reviews = []
        
        # Try to find review section
        review_selectors = [
            '[data-automation="review-list"]',
            '.reviews-list',
            '[class*="reviews"]',
            '#reviews'
        ]
        
        review_container = None
        for selector in review_selectors:
            try:
                review_container = await page.query_selector(selector)
                if review_container:
                    break
            except:
                continue
        
        if not review_container:
            return reviews
        
        # Find individual review elements
        review_item_selectors = [
            '[data-automation="review-item"]',
            '.review-item',
            '[class*="review-card"]',
            'article[class*="review"]'
        ]
        
        review_elements = []
        for selector in review_item_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    review_elements = elements
                    break
            except:
                continue
        
        for i, element in enumerate(review_elements[:20]):  # Limit to 20 reviews
            try:
                review_text_elem = await element.query_selector('[data-automation="review-text"], .review-text, [class*="comment"]')
                review_rating_elem = await element.query_selector('[data-automation="review-rating"], .review-rating, [class*="stars"]')
                review_date_elem = await element.query_selector('[data-automation="review-date"], .review-date, time')
                review_author_elem = await element.query_selector('[data-automation="review-author"], .review-author')
                
                review_data = {
                    "index": i,
                    "text": await review_text_elem.inner_text() if review_text_elem else None,
                    "rating": None,
                    "date": await review_date_elem.inner_text() if review_date_elem else None,
                    "author": await review_author_elem.inner_text() if review_author_elem else None
                }
                
                if review_rating_elem:
                    rating_text = await review_rating_elem.inner_text()
                    import re
                    match = re.search(r'(\d+[.,]?\d*)', rating_text.replace(',', '.'))
                    if match:
                        review_data["rating"] = float(match.group(1).replace(',', '.'))
                
                reviews.append(review_data)
                
            except Exception as e:
                print(f"Error extracting review {i}: {str(e)}")
                continue
        
        return reviews
    
    async def _extract_email(self, page) -> Optional[str]:
        """Extract email address from the page"""
        try:
            content = await page.content()
            
            # Common email patterns
            import re
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            
            emails = re.findall(email_pattern, content)
            
            # Filter out common non-restaurant emails
            filtered_emails = [
                email for email in emails 
                if not any(exclude in email.lower() for exclude in ['lieferando', 'takeaway', 'support', 'info'])
            ]
            
            if filtered_emails:
                return filtered_emails[0]
            elif emails:
                return emails[0]
                
        except Exception as e:
            print(f"Error extracting email: {str(e)}")
        
        return None
    
    async def search_restaurants(self, location: str, max_results: int = 10) -> List[str]:
        """Search for restaurants in a location and return URLs"""
        urls = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            
            page = await context.new_page()
            
            try:
                # Go to search page
                search_url = f"{self.base_url}/en/{location}/"
                await page.goto(search_url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(5000)
                
                # Find restaurant links
                link_selectors = [
                    'a[data-automation="restaurant-list-item"]',
                    'a[href*="/en/"][href*="/restaurant/"]',
                    '.restaurant-list a'
                ]
                
                for selector in link_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for element in elements:
                            href = await element.get_attribute('href')
                            if href and '/restaurant/' in href:
                                full_url = href if href.startswith('http') else f"{self.base_url}{href}"
                                if full_url not in urls:
                                    urls.append(full_url)
                                    if len(urls) >= max_results:
                                        break
                        if len(urls) >= max_results:
                            break
                    except:
                        continue
                
            except Exception as e:
                print(f"Error searching restaurants: {str(e)}")
            finally:
                await browser.close()
        
        return urls


async def main():
    """Example usage"""
    scraper = LieferandoScraper(headless=False, slow_mo=1500)  # Non-headless for debugging
    
    # Example 1: Scrape specific restaurant URLs
    restaurant_urls = [
        # Add your restaurant URLs here
        # "https://www.lieferando.de/en/berlin/restaurant-name-12345"
    ]
    
    results = []
    for url in restaurant_urls:
        print(f"Scraping: {url}")
        result = await scraper.scrape_restaurant(url)
        if result:
            results.append(result)
            print(f"✓ Scraped: {result.get('restaurant_name')}")
            # Save intermediate results
            with open('results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Random delay between requests
        await asyncio.sleep(random.uniform(3, 7))
    
    # Example 2: Search and scrape restaurants in a location
    # location = "berlin-mitte"
    # urls = await scraper.search_restaurants(location, max_results=5)
    # print(f"Found {len(urls)} restaurants")
    # 
    # for url in urls:
    #     result = await scraper.scrape_restaurant(url)
    #     if result:
    #         results.append(result)
    #     await asyncio.sleep(random.uniform(3, 7))
    
    # Final save
    if results:
        with open('lieferando_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(results)} results to lieferando_results.json")
    else:
        print("No results collected. Add restaurant URLs to scrape.")


if __name__ == "__main__":
    asyncio.run(main())
