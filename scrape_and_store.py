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
    "https://new.abb.com/medium-voltage/digital-substations/protection-relay-services/firmware-update-release",
    "https://www.netgear.com/support/home/downloads",
    "https://software.cisco.com/download/home/",
    "https://www.tp-link.com/in/support/download/",
    "https://downloads.openwrt.org/releases/",
    "https://www.asus.com/support/Download-Center/"
]

def fetch_content(url):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {"url": url, "pageOptions": {"waitFor": 3000}}
    response = requests.post("https://api.firecrawl.dev/v0/scrape",
                             json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

def extract_firmware(data, url):
    rows = []
    markdown = data.get("data", {}).get("markdown", "")
    if not markdown:
        return rows

    vendor_map = {
        "abb.com": "ABB",
        "netgear.com": "Netgear",
        "cisco.com": "Cisco",
        "tp-link.com": "TP-Link",
        "openwrt.org": "OpenWRT",
        "asus.com": "ASUS"
    }

    vendor = next((v for k, v in vendor_map.items() if k in url), "Unknown")

    version_pattern = r'\b[vV]?\d+\.\d+(?:\.\d+)?\b'
    versions = set(re.findall(version_pattern, markdown))

    for version in versions:
        rows.append((
            "Firmware Release",
            vendor,
            version,
            "firecrawl",
            "firmware"
        ))

    return rows

def store_firecrawl(rows):
    if not rows:
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
        CREATE TABLE IF NOT EXISTS firecraw_info (
            id SERIAL PRIMARY KEY,
            product VARCHAR(500),
            vendor VARCHAR(500),
            version VARCHAR(255),
            data_source VARCHAR(50),
            category VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(product, vendor, version)
        );
    """)

    insert_sql = """
        INSERT INTO firecraw_info
        (product, vendor, version, data_source, category)
        VALUES %s
        ON CONFLICT (product, vendor, version) DO NOTHING;
    """

    execute_values(cur, insert_sql, rows)
    conn.commit()
    cur.close()
    conn.close()

def main():
    all_rows = []
    for url in URLS:
        try:
            data = fetch_content(url)
            extracted = extract_firmware(data, url)
            all_rows.extend(extracted)
        except Exception as e:
            print(f"Error: {e}")

    store_firecrawl(all_rows)
    print("Firecrawl scraping complete.")

if __name__ == "__main__":
    main()




# import os
# import re
# import json
# import requests
# import psycopg2
# from psycopg2.extras import execute_values
# from dotenv import load_dotenv

# load_dotenv()

# # ------------------------------------------------------------
# # CONFIG
# # ------------------------------------------------------------

# API_KEY = os.getenv("FIRECRAWL_API_KEY")
# if not API_KEY:
#     raise ValueError("FIRECRAWL_API_KEY not set in environment")

# URLS = [
#     "https://new.abb.com/medium-voltage/digital-substations/protection-relay-services/firmware-update-release",
#     "https://www.netgear.com/support/home/downloads",
#     "https://software.cisco.com/download/home/",
#     "https://www.tp-link.com/in/support/download/",
#     "https://downloads.openwrt.org/releases/",
#     "https://www.asus.com/support/Download-Center/"
#     "https://www.dlink.com/en/support"
# ]

# # ------------------------------------------------------------
# # FIRECRAWL FETCH
# # ------------------------------------------------------------

# def fetch_content(url: str) -> dict:
#     headers = {"Authorization": f"Bearer {API_KEY}"}
#     payload = {
#         "url": url,
#         "pageOptions": {
#             "onlyMainContent": False,
#             "waitFor": 3000
#         }
#     }

#     print(f"Scraping: {url}")
#     response = requests.post(
#         "https://api.firecrawl.dev/v0/scrape",
#         json=payload,
#         headers=headers
#     )
#     response.raise_for_status()
#     return response.json()

# # ------------------------------------------------------------
# # EXTRACT FIRMWARE INFO
# # ------------------------------------------------------------

# def extract_rows(data: dict, url: str) -> list:
#     rows = []
#     markdown = data.get("data", {}).get("markdown", "")

#     if not markdown:
#         return rows

#     vendor_map = {
#         "abb.com": "ABB",
#         "netgear.com": "Netgear",
#         "cisco.com": "Cisco",
#         "tp-link.com": "TP-Link",
#         "openwrt.org": "OpenWRT",
#         "asus.com": "ASUS"
#     }

#     vendor = ""
#     for domain, name in vendor_map.items():
#         if domain in url:
#             vendor = name
#             break

#     # Extract version numbers like:
#     # 1.0, 1.2.3, v1.2.3, 17.3.4 etc.
#     version_pattern = r'\b[vV]?\d+\.\d+(?:\.\d+)?\b'
#     versions = re.findall(version_pattern, markdown)

#     # Remove duplicates
#     unique_versions = list(set(versions))

#     for version in unique_versions:
#         rows.append({
#             "product": "Firmware Release",
#             "vendor": vendor,
#             "version": version,
#             "category": "firmware"
#         })

#     print(f"Extracted {len(rows)} versions from {vendor}")
#     return rows

# # ------------------------------------------------------------
# # DATABASE
# # ------------------------------------------------------------

# def ensure_table_exists(cur):
#     cur.execute("""
#         CREATE TABLE IF NOT EXISTS firecraw_info (
#             id SERIAL PRIMARY KEY,
#             product VARCHAR(500),
#             vendor VARCHAR(500),
#             version VARCHAR(255),
#             data_source VARCHAR(50) DEFAULT 'firecrawl',
#             category VARCHAR(255),
#             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#             UNIQUE(product, vendor, version)
#         );
#     """)

# def store_to_db(rows: list):
#     if not rows:
#         print("No rows to insert.")
#         return

#     conn = psycopg2.connect(
#         host=os.getenv("DB_HOST", "localhost"),
#         port=os.getenv("DB_PORT", "5432"),
#         dbname=os.getenv("CVE_DB_NAME", "Baseel_CVE"),
#         user=os.getenv("DB_USER", "postgres"),
#         password=os.getenv("DB_PASSWORD")
#     )

#     cur = conn.cursor()
#     ensure_table_exists(cur)
#     conn.commit()

#     insert_sql = """
#         INSERT INTO firecraw_info
#         (product, vendor, version, data_source, category)
#         VALUES %s
#         ON CONFLICT (product, vendor, version) DO NOTHING;
#     """

#     values = [
#         (
#             r["product"],
#             r["vendor"],
#             r["version"],
#             "firecrawl",
#             r["category"]
#         )
#         for r in rows
#     ]

#     execute_values(cur, insert_sql, values)
#     conn.commit()

#     print(f"Inserted {len(values)} rows into firecraw_info.")

#     cur.close()
#     conn.close()

# # ------------------------------------------------------------
# # MAIN
# # ------------------------------------------------------------

# def main():
#     all_rows = []

#     for url in URLS:
#         try:
#             raw = fetch_content(url)

#             # Optional: save raw response for debugging
#             with open("last_response.json", "w", encoding="utf-8") as f:
#                 json.dump(raw, f, indent=2, ensure_ascii=False)

#             extracted = extract_rows(raw, url)
#             all_rows.extend(extracted)

#         except Exception as e:
#             print(f"Error scraping {url}: {e}")

#     # Remove duplicates in Python (extra safety)
#     seen = set()
#     cleaned = []
#     for r in all_rows:
#         key = (r["product"], r["vendor"], r["version"])
#         if key not in seen:
#             seen.add(key)
#             cleaned.append(r)

#     print(f"Total unique firmware entries: {len(cleaned)}")

#     store_to_db(cleaned)
#     print("Done.")

# if __name__ == "__main__":
#     main()
