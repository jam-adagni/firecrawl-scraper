import psycopg2
import os
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
# Delete rows where dataset_name contains newline or is unusually long (likely malformed vendor block)
cur.execute("DELETE FROM iot_info WHERE dataset_name LIKE '%%\n%%' OR LENGTH(dataset_name) > 200;")
deleted = cur.rowcount
conn.commit()
cur.execute('SELECT COUNT(*) FROM iot_info;')
print(f'Deleted {deleted} malformed rows. Total rows now: {cur.fetchone()[0]}')
cur.close()
conn.close()
