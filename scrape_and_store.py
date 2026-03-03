import os
import json
import re
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ------------------------------------------------------------
# Configuration (set these in the .env file)
# ------------------------------------------------------------
API_KEY = os.getenv('FIRECRAWL_API_KEY')
if not API_KEY:
    raise ValueError("FIRECRAWL_API_KEY not set in environment")

URLS = [
    "https://catalog.data.gov/dataset?tags=iot",
    "https://www.unb.ca/cic/datasets/",
]

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------

def fetch_content(url: str) -> dict:
    """Call Firecrawl API and return the JSON response."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "url": url,
        "pageOptions": {
            "onlyMainContent": False,
            "waitFor": 3000  # Wait longer for JS-rendered content
        }
    }
    print(f"Fetching content from {url}...")
    response = requests.post("https://api.firecrawl.dev/v0/scrape", json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def extract_rows(data: dict, url: str) -> list:
    """Parse the scraped markdown and extract IoT dataset information."""
    rows = []
    markdown = ""
    if "data" in data and isinstance(data["data"], dict):
        markdown = data["data"].get("markdown", "")
    else:
        markdown = data.get("markdown", "")
    if not markdown:
        print("No markdown content found in response.")
        return rows
        
        return rows
        
    if 'unb.ca/cic/datasets/' in url and not url.endswith('/datasets/') and not url.endswith('index.html'):
        # Sub-page extraction
        # Extract title from # header
        m = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
        title = m.group(1).strip() if m else ""
        
        # Extract description (first few paragraphs after the header)
        desc = ""
        paragraphs = re.findall(r'\n([^#\n\-].{20,})', markdown)
        if paragraphs:
            desc = " ".join(paragraphs[:3]).strip()
            desc = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()[:1000]
            
        # Extract year if present
        year_match = re.search(r'(\d{4})', title + desc)
        updated_date = year_match.group(1) if year_match else ""

        if title:
            # Filter out navigation/menu titles from sub-pages
            if any(word in title.lower() for word in ['search unb', 'datasets', 'about', 'contact', 'membership']):
                return []

            return [{
                "dataset_name": title,
                "source": "UNB CIC",
                "description": desc,
                "updated_date": updated_date,
                "data_format": "PCAP/CSV"
            }]
        return []

    if 'kaggle.com/datasets/' in url:
        m = re.search(r'^#\s+(.+)$', markdown, re.MULTILINE)
        if m:
            title = m.group(1).strip()
            upd = ""
            upd_match = re.search(r'Updated\s+([a-zA-Z0-9 ]+ ago)', markdown)
            if not upd_match:
                upd_match = re.search(r'Updated\s+([A-Za-z]+\s+\d+,?\s+\d{4})', markdown)
            if upd_match:
                upd = upd_match.group(1).strip()
            return [{
                "dataset_name": title,
                "source": "kaggle.com",
                "description": "",
                "updated_date": upd,
                "data_format": "csv/zip"
            }]
        return rows
        
    if 'thingspeak.mathworks.com' in url:
        pattern = re.compile(r'\*\*([^*]+)\*\*\s*[\\]*\n[\s\\]*(.*?)\]\(([^)]+)\)', re.DOTALL)
        for m in pattern.finditer(markdown):
            title = m.group(1).strip()
            desc = m.group(2).strip()
            link = m.group(3).strip()
            domain_match = re.search(r'https?://([^/]+)/', link)
            source = domain_match.group(1) if domain_match else link
            rows.append({
                "dataset_name": title,
                "source": source,
                "description": desc,
                "updated_date": "",
                "data_format": ""
            })
        return rows

    if 'shodan.io' in url:
        # Extract main section headings and their descriptions
        sections = re.findall(r'^#\s+(.+?)\n+(.*?)(?=\n#|\Z)', markdown, re.MULTILINE | re.DOTALL)
        for title, desc in sections:
            clean_title = re.sub(r'[_*]', '', title).strip()
            # Skip generic navigation headings
            if clean_title.lower() in ('', 'search engine for the internet of everything'):
                continue
            clean_desc = re.sub(r'\s+', ' ', desc).strip()
            # Remove markdown links/images from description
            clean_desc = re.sub(r'!\[.*?\]\(.*?\)', '', clean_desc)
            clean_desc = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', clean_desc)
            clean_desc = clean_desc.strip()[:500]
            if clean_title and clean_desc:
                rows.append({
                    "dataset_name": clean_title,
                    "source": "shodan.io",
                    "description": clean_desc,
                    "updated_date": "",
                    "data_format": ""
                })
        return rows

    if 'thingpark.com' in url:
        # Extract device categories from the categories section
        # Pattern: [![](image)\\\\Smart City](link)
        cat_pattern = re.compile(r'\[!\[.*?\]\(.*?\)[\\\\]*\n[\\\\]*\n([^\]]+)\]\((https://market\.thingpark\.com/devices/[^)]+)\)')
        seen_cats = set()
        for m in cat_pattern.finditer(markdown):
            cat_name = m.group(1).strip()
            cat_link = m.group(2).strip()
            if cat_name.lower() not in seen_cats:
                seen_cats.add(cat_name.lower())
                rows.append({
                    "dataset_name": cat_name,
                    "source": "market.thingpark.com",
                    "description": f"IoT device category on ThingPark Market",
                    "updated_date": "",
                    "data_format": ""
                })
        # Also extract vendor/seller names
        seller_pattern = re.findall(r'\n([A-Z][A-Za-z0-9\s&.,()®\-]+(?:Ltd|GmbH|Inc|Corp|Srl|OÜ|AB|B\.V\.|co\.|Co\.)\.?)\s*$', markdown, re.MULTILINE)
        for seller in seller_pattern:
            seller = seller.strip()
            if seller and len(seller) > 3 and seller.lower() not in seen_cats:
                seen_cats.add(seller.lower())
                rows.append({
                    "dataset_name": seller,
                    "source": "market.thingpark.com",
                    "description": "IoT device vendor/seller on ThingPark Market",
                    "updated_date": "",
                    "data_format": ""
                })
        return rows

    if 'ipros.com' in url:
        product_blocks = re.split(r'###\s+\[', markdown)
        for block in product_blocks[1:]:
            title_match = re.match(r'([^\]]+)\]\((https://mono\.ipros\.com/en/product/detail/[^)]+)\)', block)
            if not title_match:
                continue
            title = title_match.group(1).strip()
            
            desc_match = re.search(r'\)\n+(.*?)\n+\-\s+Company：', block, re.DOTALL)
            desc = desc_match.group(1).strip() if desc_match else ""
            desc = re.sub(r'[*_]', '', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            desc = desc[:500]
            
            company_match = re.search(r'\-\s+Company：\s*\[([^\]]+)\]', block)
            company = company_match.group(1).strip() if company_match else "mono.ipros.com"
            
            title = re.sub(r'\[.*?\]\s*', '', title).strip()
            
            rows.append({
                "dataset_name": title,
                "source": company,
                "description": desc,
                "updated_date": "",
                "data_format": ""
            })
        return rows

    if 'data.gov' in url:
        blocks = re.split(r'###\s+\[', markdown)
        for block in blocks[1:]:
            title_match = re.match(r'([^\]]+)\]\((https?://catalog\.data\.gov/dataset/[^)]+)\)', block)
            if not title_match: continue
            title = title_match.group(1).strip()
            
            company_desc_match = re.search(r'\)\n+\s*(.+?)\s*—\n+\s*(.*?)\n+\s*\-', block, re.DOTALL)
            if company_desc_match:
                company = company_desc_match.group(1).strip()
                desc = company_desc_match.group(2).strip()
            else:
                company_desc_match = re.search(r'\)\n+\s*(.+?)\s*—\n+\s*(.*)', block, re.DOTALL)
                if company_desc_match:
                    company = company_desc_match.group(1).strip()
                    desc = company_desc_match.group(2).strip()
                else:
                    company = "data.gov"
                    desc = ""
            
            desc = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            desc = desc[:500]
            
            formats_match = re.findall(r'\-\s+\[(CSV|JSON|RDF|XML|GeoJSON|SHP|HTML|ZIP|TEXT)\]', block, re.IGNORECASE)
            data_format = ",".join(list(set(formats_match))) if formats_match else ""
            
            rows.append({
                "dataset_name": title,
                "source": company,
                "description": desc,
                "updated_date": "",
                "data_format": data_format
            })
        return rows

    if 'unb.ca' in url:
        # Pattern: - [Name](Link)
        # Narrow down to links within the cic/datasets path to avoid navigation links
        pattern = re.compile(r'[-*]\s+\[([^\]]+)\]\((https?://(?:www\.)?unb\.ca/+[Cc][Ii][Cc]/[Dd][Aa][Tt][Aa][Ss][Ee][Tt][Ss]/([^)]+))\)')
        for m in pattern.finditer(markdown):
            title = m.group(1).strip()
            link_path = m.group(3).strip()
            
            # Filter out navigation links, anchors, and index pages
            if '#' in link_path or 'index.html' in link_path.lower():
                continue
            
            # Filter out generic links or links that look like menu items
            if len(title) < 5 or any(word in title.lower() for word in ['skip to', 'contact us', 'about the cic', 'membership', 'webinars', 'global epic', 'workshop']):
                continue

            # Extract year if present in title
            year_match = re.search(r'(\d{4})', title)
            updated_date = year_match.group(1) if year_match else ""
            
            rows.append({
                "dataset_name": title,
                "source": "UNB CIC",
                "description": "Cybersecurity dataset from Canadian Institute for Cybersecurity",
                "updated_date": updated_date,
                "data_format": "PCAP/CSV",
                "sub_url": f"https://www.unb.ca/cic/datasets/{link_path.replace('//', '/')}"
            })
        return rows
    
    # Split text into dataset blocks (01., 02., etc.), ignoring trailing footer content
    blocks = re.findall(r'\n\d{2}\. (.*?)(?=\n\d{2}\. |\nShare|\nShare|\Z)', '\n' + markdown, re.DOTALL)
    
    for block in blocks:
        block = block.strip()
        if not block: continue
        
        # Heading
        title_match = re.search(r'#\s+(.+)', block)
        if not title_match: continue
        title = title_match.group(1).strip()
        
        # Sources
        sources = re.findall(r'^\s*-\s+(.+)$', block, re.MULTILINE)
        sources = [s.strip() for s in sources]
        source_str = ", ".join(sources)
        
        # Updated date
        updated_match = re.search(r'Updated\s+([A-Za-z]+\s+\d+,?\s+\d{4})', block)
        updated_date = updated_match.group(1).strip() if updated_match else ""
        
        # Data format
        format_match = re.search(r'^(zip|pcap|csv|pdf|excel|ppt|pdf,excel,csv,ppt)$', block, re.MULTILINE | re.IGNORECASE)
        data_format = format_match.group(1).strip() if format_match else ""
        
        # To avoid duplicates
        if not any(r["dataset_name"].lower() == title.lower() for r in rows):
            rows.append({
                "dataset_name": title,
                "source": source_str,
                "description": "",
                "updated_date": updated_date,
                "data_format": data_format,
            })
            
    # Strategy 2: UNSW / Simple Markdown lists
    lines = markdown.split('\n')
    current_name = None
    current_sources = []
    for line in lines:
        line = line.strip()
        heading_match = re.match(r'^#{1,3}\s+(.+)$', line)
        if heading_match:
            if current_name and current_sources:
                 if not any(r["dataset_name"].lower() == current_name.lower() for r in rows):
                    rows.append({
                        "dataset_name": current_name,
                        "source": ", ".join(current_sources),
                        "description": "",
                        "updated_date": "",
                        "data_format": "",
                    })
            current_name = heading_match.group(1).strip()
            current_sources = []
            continue
        source_match = re.match(r'^[-*]\s+(.+)$', line)
        if source_match and current_name:
            src = source_match.group(1).strip()
            link_match = re.search(r'\[([^\]]*)\]\(([^)]+)\)', src)
            if link_match:
                src = link_match.group(2)
            current_sources.append(src)
    if current_name and current_sources:
        if not any(r["dataset_name"].lower() == current_name.lower() for r in rows):
            rows.append({
                "dataset_name": current_name,
                "source": ", ".join(current_sources),
                "description": "",
                "updated_date": "",
                "data_format": "",
            })

    return rows


def clean_rows(rows: list) -> list:
    """Deduplicate rows based on dataset name (case‑insensitive)."""
    filtered = [r for r in rows if r.get("dataset_name")]
    seen = set()
    unique = []
    for r in filtered:
        key = r["dataset_name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def ensure_table_exists(cur) -> None:
    """Create a fresh iot_info table with the correct schema if it doesn't already exist."""
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


def store_to_db(rows: list) -> None:
    """Insert rows into the iot_info table."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            dbname=os.getenv('CVE_DB_NAME', 'Baseel_CVE'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        # Ensure table exists with correct schema
        ensure_table_exists(cur)
        conn.commit()
        insert_sql = """
            INSERT INTO iot_info (dataset_name, source, description, updated_date, data_format, data_source)
            VALUES %s
            ON CONFLICT (dataset_name, source) DO NOTHING;
        """
        values = [(
            r["dataset_name"],
            r["source"],
            r["description"],
            r["updated_date"],
            r.get("data_format", ""),
            "firecrawl"
        ) for r in rows]
        execute_values(cur, insert_sql, values)
        conn.commit()
        print(f"Inserted {len(values)} rows into iot_info.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error storing to DB: {e}")

def main() -> None:
    all_rows = []
    sub_urls = []
    for url in URLS:
        try:
            raw = fetch_content(url)
            # Save raw response for debugging
            with open('last_response.json', 'w', encoding='utf-8') as f:
                json.dump(raw, f, indent=2, ensure_ascii=False)
            extracted = extract_rows(raw, url)
            print(f"Extracted {len(extracted)} items from {url}")
            
            for item in extracted:
                if item.get("sub_url"):
                    sub_urls.append(item["sub_url"])
                else:
                    all_rows.append(item)
                    
        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Deep scrape UNB sub-urls for detailed info
    if sub_urls:
        print(f"Deep scraping {len(sub_urls)} sub-pages from UNB...")
        for sub_url in sub_urls:
            try:
                raw = fetch_content(sub_url)
                extracted = extract_rows(raw, sub_url)
                if extracted:
                    all_rows.extend(extracted)
                    print(f"Extracted details for: {extracted[0]['dataset_name']}")
            except Exception as e:
                print(f"Error deep scraping {sub_url}: {e}")

    if all_rows:
        cleaned = clean_rows(all_rows)
        print(f"After deduplication: {len(cleaned)} unique rows")
        # Show a short preview
        for i, r in enumerate(cleaned[:10], 1):
            print(f"{i}. {r['dataset_name']} (source: {r['source']})")
        store_to_db(cleaned)
    else:
        print("No rows extracted.")
    print("Scraping complete.")

if __name__ == "__main__":
    main()
