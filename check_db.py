import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def list_tables():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('CVE_DB_NAME', 'Baseel_CVE'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
        
    for table in tables:
        print(f"\nColumns in {table[0]}:")
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table[0]}'
        """)
        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
    
    # Show iot_info data if table exists
    try:
        cur.execute("SELECT COUNT(*) FROM iot_info")
        count = cur.fetchone()[0]
        print(f"\n--- iot_info table: {count} records ---")
        if count > 0:
            cur.execute("SELECT dataset_name, source, updated_date, data_format FROM iot_info LIMIT 20")
            rows = cur.fetchall()
            for i, row in enumerate(rows, 1):
                print(f"{i}. {row[0]}")
                print(f"   Source: {row[1]}")
                if row[2]:
                    print(f"   Updated: {row[2]}")
                if row[3]:
                    print(f"   Format: {row[3]}")
    except Exception:
        print("\niot_info table does not exist yet.")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_tables()
