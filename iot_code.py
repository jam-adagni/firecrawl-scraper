import os
import re
import json
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FIRECRAWL_API_KEY")

URLS = [
    "https://www.unb.ca/cic/datasets/iotdataset-2023.html",
    "https://datasetsearch.research.google.com/search?query=iot",
    "https://research.unsw.edu.au/projects/toniot-datasets",
    "https://www.data.gouv.fr/datasets/dataset-of-legitimate-iot-data/",
    "https://www.kaggle.com/datasets/azalhowaide/iot-dataset-for-intrusion-detection-systems-ids",
    "https://sites.unica.it/net4u/siot-iot-network-dataset/",
    "https://thingspeak.mathworks.com/",
    "https://www.shodan.io/"
]

# ------------------------------------------------------------
# FETCH
# ------------------------------------------------------------

def fetch_content(url):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "url": url,
        "pageOptions": {
            "onlyMainContent": False,
            "waitFor": 3000
        }
    }

    print(f"Scraping: {url}")
    response = requests.post(
        "https://api.firecrawl.dev/v0/scrape",
        json=payload,
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# ------------------------------------------------------------
# EXTRACT GENERIC DATASET INFO
# ------------------------------------------------------------

def extract_dataset_info(data, url):
    rows = []
    markdown = data.get("data", {}).get("markdown", "")

    if not markdown:
        return rows

    # Extract main title
    title_match = re.search(r'^#\s+(.+)', markdown, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else url

    # Extract first paragraph as description
    paragraphs = re.findall(r'\n([^#\n\-].{30,})', markdown)
    description = paragraphs[0].strip() if paragraphs else ""

    # Clean markdown links
    description = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', description)
    description = re.sub(r'\s+', ' ', description)[:800]

    rows.append((
        title,
        url,
        description,
        "",
        "",
        "firecrawl"
    ))

    return rows

# ------------------------------------------------------------
# STORE TO iot_info
# ------------------------------------------------------------

def store_iot(rows):
    if not rows:
        print("No rows extracted.")
        return

    conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('CVE_DB_NAME', 'Baseel_CVE'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
    )

    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS iot_info (
            id SERIAL PRIMARY KEY,
            dataset_name TEXT NOT NULL,
            source TEXT,
            description TEXT,
            updated_date TEXT,
            data_format TEXT,
            data_source TEXT DEFAULT 'firecrawl',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(dataset_name, source)
        );
    """)

    insert_sql = """
        INSERT INTO iot_info
        (dataset_name, source, description, updated_date, data_format, data_source)
        VALUES %s
        ON CONFLICT (dataset_name, source) DO NOTHING;
    """

    execute_values(cur, insert_sql, rows)
    conn.commit()

    print(f"Inserted {len(rows)} rows into iot_info.")

    cur.close()
    conn.close()

# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    all_rows = []

    for url in URLS:
        try:
            data = fetch_content(url)

            # optional debug save
            with open("last_iot_response.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            extracted = extract_dataset_info(data, url)
            all_rows.extend(extracted)

        except Exception as e:
            print(f"Error scraping {url}: {e}")

    # Deduplicate manually
    unique = {}
    for row in all_rows:
        key = (row[0], row[1])
        if key not in unique:
            unique[key] = row

    store_iot(list(unique.values()))
    print("IoT scraping complete.")

if __name__ == "__main__":
    main()
