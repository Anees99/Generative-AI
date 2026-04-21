# Lieferando.de Scraper - Setup & Usage Guide

## ⚠️ Important Legal Notice

**Before using this scraper:**
- Review [lieferando.de Terms of Service](https://www.lieferando.de/en/terms-and-conditions/)
- Check their `robots.txt` file at `https://www.lieferando.de/robots.txt`
- This tool is for **educational purposes only**
- Do not use for commercial purposes without explicit permission
- Respect rate limits and avoid overloading their servers
- Email scraping may violate GDPR regulations

## Prerequisites

You need:
- Python 3.8 or higher
- pip (Python package manager)
- Adequate disk space (~200MB for browser installation)

## Installation Steps

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install playwright>=1.40.0
```

### Step 2: Install Playwright Browsers

```bash
playwright install chromium
```

This downloads Chromium browser (~150MB) required for automation.

**Note:** If you encounter "no space left on device" error, free up disk space or install on a different drive.

### Step 3: Verify Installation

```bash
python -c "from playwright.async_api import async_playwright; print('Playwright installed successfully!')"
```

## How to Run

### Option 1: Scrape Specific Restaurant URLs

1. Edit `lieferando_scraper.py` and add restaurant URLs to the `restaurant_urls` list in the `main()` function:

```python
restaurant_urls = [
    "https://www.lieferando.de/en/berlin/restaurant-name-12345",
    "https://www.lieferando.de/en/munich/another-restaurant-67890",
    # Add more URLs here
]
```

2. Run the scraper:
```bash
python lieferando_scraper.py
```

3. Results will be saved to `lieferando_results.json`

### Option 2: Search by Location

Uncomment and modify the search section in `main()`:

```python
location = "berlin-mitte"  # Change to your desired location
urls = await scraper.search_restaurants(location, max_results=5)

for url in urls:
    result = await scraper.scrape_restaurant(url)
    if result:
        results.append(result)
    await asyncio.sleep(random.uniform(3, 7))  # Rate limiting
```

### Option 3: Use as a Module

```python
import asyncio
from lieferando_scraper import LieferandoScraper

async def main():
    scraper = LieferandoScraper(headless=True, slow_mo=1000)
    
    # Scrape a single restaurant
    result = await scraper.scrape_restaurant("https://www.lieferando.de/en/...")
    print(result)
    
    # Or search for restaurants
    urls = await scraper.search_restaurants("berlin", max_results=10)
    print(f"Found {len(urls)} restaurants")

asyncio.run(main())
```

## Configuration Options

### Scraper Settings

```python
scraper = LieferandoScraper(
    headless=True,      # True = no browser UI, False = show browser
    slow_mo=1000        # Delay in ms between actions (higher = slower but less detectable)
)
```

### Rate Limiting

The script includes built-in delays:
- `slow_mo=1000`: 1 second delay between browser actions
- `asyncio.sleep(random.uniform(3, 7))`: 3-7 seconds between restaurant scrapes

**Adjust these values to be more respectful:**
```python
scraper = LieferandoScraper(headless=True, slow_mo=2000)  # Slower
await asyncio.sleep(random.uniform(5, 10))  # Longer delays
```

## Output Format

Results are saved as JSON:

```json
[
  {
    "url": "https://www.lieferando.de/en/...",
    "restaurant_name": "Restaurant Name",
    "company_name": "Legal Company Name",
    "rating": 4.5,
    "reviews_count": 150,
    "reviews": [
      {
        "index": 0,
        "text": "Great food!",
        "rating": 5.0,
        "date": "2024-01-15",
        "author": "John D."
      }
    ],
    "email": "contact@restaurant.com",
    "scraped_at": 1234567890.123
  }
]
```

## Troubleshooting

### "No space left on device"
- Free up disk space (need ~200MB)
- Install browsers to a different location
- Use existing browser: `BROWSER_PATH=/usr/bin/chromium-browser python script.py`

### "TimeoutError"
- Increase timeout in `page.goto()` call
- Check your internet connection
- The website might be blocking automated access

### "Element not found"
- Website structure may have changed
- Selectors in the script need updating
- Try running with `headless=False` to debug visually

### Captcha or Blocking
- Reduce scraping speed (increase `slow_mo` and delays)
- Add more realistic user agents
- Consider using residential proxies
- **Stop scraping if consistently blocked**

## Best Practices

1. **Start Small**: Test with 1-2 restaurants first
2. **Respect Rate Limits**: Don't scrape too fast
3. **Monitor Errors**: Check console output for issues
4. **Save Progress**: Results auto-save after each restaurant
5. **Be Ethical**: Only scrape publicly available data
6. **Check Changes**: Website updates may break the scraper

## Alternative Approaches

If scraping fails repeatedly:
- Check if Lieferando offers an official API
- Consider manual data collection for small datasets
- Look for alternative data sources
- Contact restaurants directly for information

## Support

For issues:
1. Check the error message carefully
2. Run with `headless=False` to see what's happening
3. Verify the restaurant URL works in a regular browser
4. Review Lieferando's terms of service

---

**Remember**: Web scraping should be done responsibly and legally. Always respect website terms of service and applicable laws.
