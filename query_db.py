import json
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
cur.execute("SELECT dataset_name, source, data_format, updated_date FROM iot_info LIMIT 20")
columns = [desc[0] for desc in cur.description]
data = [dict(zip(columns, row)) for row in cur.fetchall()]
cur.close()
conn.close()

with open('db_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
