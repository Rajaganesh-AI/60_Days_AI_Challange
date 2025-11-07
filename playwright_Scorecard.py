import asyncio
from playwright.async_api import async_playwright

async def main():
    # Start Playwright
    async with async_playwright() as p:
        # Launch browser (headful mode so you can see it)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Cricbuzz URL for India Women vs South Africa Women Final
        # (You can update this if the match link changes)
        url = "https://www.cricbuzz.com/live-cricket-scorecard/121681/indw-vs-rsaw-final-icc-womens-world-cup-2025"
        
        print(f"Opening {url} ...")
        await page.goto(url, wait_until="load")

        # Wait for scorecard to load
        #await page.wait_for_selector(".cb-col.cb-col-100.cb-ltst-wgt-hdr")

        print("✅ Cricbuzz scorecard page loaded successfully!")

        # Keep browser open until manually closed
        await asyncio.sleep(30)

        await browser.close()

# Run the script
asyncio.run(main())
