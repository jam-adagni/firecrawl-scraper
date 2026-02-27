import os
import requests
from bs4 import BeautifulSoup
import psycopg2
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=os.getenv('DB_PORT', '5432'),
    dbname=os.getenv('CVE_DB_NAME', 'Baseel_CVE'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD')
)

cur = conn.cursor()

def fetch_page(page_num):
    url = f"https://thingspeak.mathworks.com/channels/public?page={page_num}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching page {page_num}: {e}")
        return None

def parse_page(html):
    rows = []
    if not html: return rows
    soup = BeautifulSoup(html, 'html.parser')
    channel_tiles = soup.find_all('div', class_='card channel-card')
    for tile in channel_tiles:
        channel_header = tile.find('div', class_='card-header')
        if not channel_header: continue
        
        # Link and title are both grouped inside card-header, we want the second a tag which has the title without icon
        a_tags = channel_header.find_all('a')
        if not a_tags or len(a_tags) < 2: continue
        title_a_tag = a_tags[1]
        title = title_a_tag.text.strip()
        link = "https://thingspeak.mathworks.com" + title_a_tag['href']
        
        desc_p = tile.find('p', class_='public_channel_description')
        desc = desc_p.text.strip() if desc_p else ""
        desc = desc[:500]
        
        tags_div = tile.find('div', class_='public_channel_tags')
        tags = []
        if tags_div:
            tags = [t.text.strip() for t in tags_div.find_all('a')]
        
        rows.append({
            "dataset_name": title,
            "source": link,
            "description": desc,
            "updated_date": "",
            "data_format": ",".join(tags)[:250]
        })
    return rows

def scrape_all():
    all_rows = []
    pages_to_fetch = list(range(1, 75)) # 74 pages * 15 = roughly 1100 records
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        html_pages = list(executor.map(fetch_page, pages_to_fetch))
        
    for html in html_pages:
        all_rows.extend(parse_page(html))
        
    print(f"Scraped {len(all_rows)} rows. Inserting into DB...")
    
    inserted = 0
    for row in all_rows:
        try:
            cur.execute("""
                INSERT INTO iot_info (dataset_name, source, description, updated_date, data_format, data_source)
                VALUES (%s, %s, %s, %s, %s, 'thingspeak_fast')
                ON CONFLICT (dataset_name, source) DO NOTHING
            """, (
                row["dataset_name"],
                row["source"],
                row["description"],
                row["updated_date"],
                row["data_format"],
            ))
            if cur.rowcount > 0:
                inserted += 1
        except psycopg2.Error as e:
            conn.rollback()
            print(f"DB Error on {row['dataset_name']}: {e}")
            continue
        else:
            conn.commit()
            
    print(f"Inserted {inserted} new records.")

if __name__ == "__main__":
    scrape_all()
    cur.execute("SELECT COUNT(*) FROM iot_info;")
    print(f"Total records in DB: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
