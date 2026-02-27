import os
import requests
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

def fetch_page(start_num):
    url = "http://prf.cert.wi-fi.org/products/view/filtered"
    params = {
        "sort_by": "default",
        "sort_order": "desc",
        "start": start_num * 10,
        "items": 10
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching start {start_num}: {e}")
        return None

def parse_page(json_data):
    rows = []
    if not json_data or "items" not in json_data:
        return rows
    
    for item in json_data["items"]:
        p_id = item.get("id", "")
        title = item.get("name", "Unknown")
        variant = item.get("variantName")
        if variant:
            title = f"{title} - {variant}"
        if p_id:
            title = f"{title} (ID:{p_id})"
            
        company = item.get("companyName", "wi-fi.org")
        
        desc = item.get("description") or ""
        desc = desc[:500]
        
        category = item.get("productCategory", {}).get("name", "")
        freq = item.get("frequencyBand", "")
        tags = []
        if category: tags.append(category)
        if freq: tags.append(freq)
        cert_text = ",".join(tags)[:250]
        
        updated = item.get("certified", "")
        
        rows.append({
            "dataset_name": title[:250],
            "source": company[:250],
            "description": desc,
            "updated_date": updated[:250],
            "data_format": cert_text
        })
    return rows

def scrape_all():
    all_rows = []
    # 150 requests * 10 items = ~1500 records
    starts_to_fetch = list(range(0, 150))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        json_pages = list(executor.map(fetch_page, starts_to_fetch))
        
    for j_data in json_pages:
        all_rows.extend(parse_page(j_data))
        
    print(f"Scraped {len(all_rows)} rows. Inserting into DB...")
    
    inserted = 0
    for row in all_rows:
        try:
            cur.execute("""
                INSERT INTO iot_info (dataset_name, source, description, updated_date, data_format, data_source)
                VALUES (%s, %s, %s, %s, %s, 'wi-fi.org')
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
