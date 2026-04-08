import { PlaywrightCrawler, Dataset, log } from 'crawlee';

// ============================================================================
// UBEREATS SCRAPER
// Built with Crawlee (PlaywrightCrawler)
// ============================================================================

const crawler = new PlaywrightCrawler({
    // Use headless mode for performance
    headless: true,
    
    // Handle requests
    async requestHandler({ page, request, enqueueLinks }) {
        const { url, userData } = request;
        log.info(`Processing ${url}...`);

        // ====================================================================
        // WAKE-UP TRICK
        // Start URL: https://example.com
        // Reads target city/postal code from customData.locations array
        // ====================================================================
        if (url === 'https://example.com/' || url === 'https://example.com') {
            const locations = userData.customData?.locations || ['New York'];
            for (const location of locations) {
                // Construct search URL for the location
                // Note: UberEats search URLs can be complex, this is a simplified example
                const searchUrl = `https://www.ubereats.com/city/${encodeURIComponent(location.toLowerCase().replace(/\s+/g, '-'))}`;
                await crawler.addRequests([{ url: searchUrl, label: 'LISTING' }]);
            }
            return;
        }

        // ====================================================================
        // LISTING PAGE
        // Urls containing '/city/' or location based listing pages
        // ====================================================================
        if (request.label === 'LISTING' || url.includes('/city/') || url.includes('/location/')) {
            log.info(`Scraping listing page: ${url}`);
            
            // Scroll down to load all restaurant cards
            await page.evaluate(async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeight - window.innerHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            });

            // Wait for some restaurant links to appear
            await page.waitForSelector('a[href*="/store/"]', { timeout: 10000 }).catch(() => log.warning('No store links found on listing page.'));

            // Extract all restaurant page links and enqueue them
            await enqueueLinks({
                selector: 'a[href*="/store/"]',
                label: 'RESTAURANT',
                strategy: 'all',
            });
            
            // Handle pagination if available (e.g., "Next" button)
            const nextButton = await page.$('button[aria-label="Next"]');
            if (nextButton) {
                const isEnabled = await page.evaluate(btn => !btn.disabled, nextButton);
                if (isEnabled) {
                    await Promise.all([
                        page.waitForNavigation({ waitUntil: 'networkidle' }),
                        nextButton.click(),
                    ]);
                    // Re-enqueue the new page URL as a listing
                    await crawler.addRequests([{ url: page.url(), label: 'LISTING' }]);
                }
            }
        }

        // ====================================================================
        // RESTAURANT PAGE
        // Urls containing '/store/'
        // ====================================================================
        if (request.label === 'RESTAURANT' || url.includes('/store/')) {
            log.info(`Scraping restaurant page: ${url}`);
            
            // Wait for page to fully load
            await page.waitForLoadState('networkidle');

            // Helper function to safely extract text
            const extractText = async (selector) => {
                try {
                    const el = await page.$(selector);
                    return el ? await el.innerText() : null;
                } catch (e) {
                    return null;
                }
            };

            // Extract JSON-LD structured data as first source
            const jsonLdData = await page.evaluate(() => {
                const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
                for (const script of scripts) {
                    try {
                        const data = JSON.parse(script.textContent);
                        if (data['@type'] === 'Restaurant' || data['@type'] === 'FoodEstablishment') {
                            return data;
                        }
                    } catch (e) {
                        // Ignore parse errors
                    }
                }
                return null;
            });

            // Initialize data object with nulls per STRICT RULES
            // Output format per restaurant
            const data = {
                restaurantName: null,
                streetAddress: null,
                city: null,
                postalCode: null,
                phone: null,
                email: null,
                website: null,
                cuisine: null,
                rating: null,
                reviewCount: null,
                deliveryFee: null,
                deliveryTime: null,
                priceRange: null,
                uberEatsUrl: url
            };

            // 1. Try to populate from JSON-LD first
            if (jsonLdData) {
                data.restaurantName = jsonLdData.name || null;
                if (jsonLdData.address) {
                    data.streetAddress = jsonLdData.address.streetAddress || null;
                    data.city = jsonLdData.address.addressLocality || null;
                    data.postalCode = jsonLdData.address.postalCode || null;
                }
                data.phone = jsonLdData.telephone || null;
                data.email = jsonLdData.email || null;
                data.website = jsonLdData.url || null;
                data.cuisine = jsonLdData.servesCuisine ? (Array.isArray(jsonLdData.servesCuisine) ? jsonLdData.servesCuisine.join(', ') : jsonLdData.servesCuisine) : null;
                if (jsonLdData.aggregateRating) {
                    data.rating = jsonLdData.aggregateRating.ratingValue ? parseFloat(jsonLdData.aggregateRating.ratingValue) : null;
                    data.reviewCount = jsonLdData.aggregateRating.reviewCount ? parseInt(jsonLdData.aggregateRating.reviewCount, 10) : null;
                }
                data.priceRange = jsonLdData.priceRange || null;
            }

            // 2. Fallback to CSS selectors for missing fields
            // Add error handling so one failed field never crashes the whole scraper
            try {
                if (!data.restaurantName) {
                    data.restaurantName = await extractText('h1');
                }
                
                if (!data.streetAddress || !data.city || !data.postalCode) {
                    const addressText = await extractText('button:has-text(",")') || await extractText('[data-testid="store-address"]');
                    if (addressText) {
                        const parts = addressText.split(',').map(p => p.trim());
                        if (parts.length >= 3) {
                            if (!data.streetAddress) data.streetAddress = parts[0];
                            if (!data.city) data.city = parts[1];
                            if (!data.postalCode) {
                                const stateZip = parts[2].split(' ');
                                data.postalCode = stateZip.length > 1 ? stateZip[stateZip.length - 1] : null;
                            }
                        }
                    }
                }

                // STRICT RULES: NEVER generate fake phone numbers, email addresses, or guess contact info.
                // Only extract if a real phone number is visibly displayed on the page.
                if (!data.phone) {
                    const phoneMatch = await page.evaluate(() => {
                        const bodyText = document.body.innerText;
                        // Basic regex to find phone numbers explicitly on the page
                        const match = bodyText.match(/(?:\+?1[-.●]?)?\(?([0-9]{3})\)?[-.●]?([0-9]{3})[-.●]?([0-9]{4})/);
                        return match ? match[0] : null;
                    });
                    if (phoneMatch) data.phone = phoneMatch;
                }

                if (!data.cuisine) {
                    data.cuisine = await extractText('[data-testid="store-info-categories"]') || await extractText('div:has-text("•")');
                }

                if (!data.rating) {
                    const ratingText = await extractText('[data-testid="store-rating"]');
                    if (ratingText) {
                        const match = ratingText.match(/([\d.]+)/);
                        if (match) data.rating = parseFloat(match[1]);
                    }
                }

                if (!data.reviewCount) {
                    const reviewText = await extractText('[data-testid="store-rating"]');
                    if (reviewText) {
                        const match = reviewText.match(/\(([\d,+]+)\)/);
                        if (match) data.reviewCount = parseInt(match[1].replace(/,/g, ''), 10);
                    }
                }

                if (!data.deliveryFee) {
                    const feeText = await extractText('[data-testid="delivery-fee"]');
                    if (feeText) data.deliveryFee = feeText.replace(/Delivery Fee/i, '').trim();
                }

                if (!data.deliveryTime) {
                    const timeText = await extractText('[data-testid="delivery-time"]');
                    if (timeText) data.deliveryTime = timeText.trim();
                }

                if (!data.priceRange) {
                    const priceText = await page.evaluate(() => {
                        const els = Array.from(document.querySelectorAll('span'));
                        const priceEl = els.find(el => el.innerText.match(/^\$+$/));
                        return priceEl ? priceEl.innerText : null;
                    });
                    if (priceText) data.priceRange = priceText;
                }

            } catch (error) {
                log.error(`Error extracting data with CSS selectors on ${url}: ${error.message}`);
            }

            // Push data to dataset
            await Dataset.pushData(data);
            log.info(`Successfully scraped data for ${data.restaurantName || url}`);
        }
    },
    
    // Failed request handler
    failedRequestHandler({ request, log }) {
        log.error(`Request ${request.url} failed too many times.`);
    },
});

// ============================================================================
// EXECUTION
// ============================================================================

const customData = {
    locations: ['San Francisco', 'New York', 'Los Angeles']
};

await crawler.run([
    {
        url: 'https://example.com',
        userData: { customData }
    }
]);
