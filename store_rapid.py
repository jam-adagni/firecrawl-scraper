import os
import json
import psycopg2
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

def store_rapid():
    with open('rapid_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} items from JSON.")
    
    inserted = 0
    for item in data:
        name = item.get('name', 'Unknown')
        r_id = item.get('id', '')
        if r_id:
            dataset_name = f"{name} (RapidAPI ID: {r_id})"
        else:
            dataset_name = name
            
        source = item.get('categoryName', 'RapidAPI Hub')
        desc = item.get('description', '')
        
        # limit lengths
        dataset_name = dataset_name[:250]
        source = source[:250]
        desc = desc[:500]
        
        try:
            cur.execute("""
                INSERT INTO iot_info (dataset_name, source, description, updated_date, data_format, data_source)
                VALUES (%s, %s, %s, %s, %s, 'RapidAPI')
                ON CONFLICT (dataset_name, source) DO NOTHING
            """, (
                dataset_name,
                source,
                desc,
                'RapidAPI Hub',
                source # Use category as format for now
            ))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            conn.rollback()
            print(f"Error inserting {dataset_name}: {e}")
            continue
        else:
            conn.commit()
            
    print(f"Successfully inserted {inserted} new records.")

if __name__ == "__main__":
    store_rapid()
    cur.execute("SELECT COUNT(*) FROM iot_info;")
    print(f"Total records in DB: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
