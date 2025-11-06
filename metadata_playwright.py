from playwright.sync_api import sync_playwright
import time

def get_all_meta_data(output_path="google_metadata.txt"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.google.com")

        # Wait extra time to ensure dynamic meta tags load
        time.sleep(3)  # optional, adjust if needed

        # Extract all meta tags from entire document
        meta_tags = page.eval_on_selector_all(
            "meta",
            """(elements) => elements.map(el => {
                let attrs = {};
                for (let a of el.attributes) attrs[a.name] = a.value;
                return attrs;
            })"""
        )

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            for i, tag in enumerate(meta_tags, 1):
                f.write(f"Meta Tag #{i}\n")
                for attr, val in tag.items():
                    f.write(f"  {attr}: {val}\n")
                f.write("\n")

        browser.close()
        print(f"✅ Metadata saved to {output_path}")

if __name__ == "__main__":
    get_all_meta_data("C:/Users/sloch/Documents/google_metadata.txt")
