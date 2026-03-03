import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------
# LOAD ENV
# ------------------------------------------------------------

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "Baseel_CVE"
DB_USER = "postgres"
DB_PASSWORD = "postgree"

def list_tables():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()

    # ------------------------------------------------------------
    # LIST TABLES
    # ------------------------------------------------------------
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()

    print("\n=== TABLES IN DATABASE ===")
    for table in tables:
        print(f"- {table[0]}")

    # ------------------------------------------------------------
    # SHOW COLUMNS
    # ------------------------------------------------------------
    for table in tables:
        table_name = table[0]
        print(f"\n=== COLUMNS IN {table_name} ===")

        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))

        columns = cur.fetchall()
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")

    # ------------------------------------------------------------
    # PREVIEW firecraw_info
    # ------------------------------------------------------------
    try:
        cur.execute("SELECT COUNT(*) FROM firecraw_info;")
        count = cur.fetchone()[0]

        print(f"\n--- firecraw_info: {count} records ---")

        if count > 0:
            cur.execute("""
                SELECT product, vendor, version, category
                FROM firecraw_info
                ORDER BY created_at DESC
                LIMIT 10;
            """)
            rows = cur.fetchall()

            for i, row in enumerate(rows, 1):
                print(f"{i}. Product: {row[0]}")
                print(f"   Vendor: {row[1]}")
                print(f"   Version: {row[2]}")
                print(f"   Category: {row[3]}")

    except Exception:
        print("\nfirecraw_info table does not exist.")

    # ------------------------------------------------------------
    # PREVIEW iot_info
    # ------------------------------------------------------------
    try:
        cur.execute("SELECT COUNT(*) FROM iot_info;")
        count = cur.fetchone()[0]

        print(f"\n--- iot_info: {count} records ---")

        if count > 0:
            cur.execute("""
                SELECT dataset_name, source, data_source
                FROM iot_info
                ORDER BY created_at DESC
                LIMIT 10;
            """)
            rows = cur.fetchall()

            for i, row in enumerate(rows, 1):
                print(f"{i}. Dataset: {row[0]}")
                print(f"   Source URL: {row[1]}")
                print(f"   Data Source: {row[2]}")

    except Exception:
        print("\niot_info table does not exist.")

    cur.close()
    conn.close()


if __name__ == "__main__":
    list_tables()


# import os
# import psycopg2
# from dotenv import load_dotenv

# load_dotenv()

# def list_tables():
#     conn = psycopg2.connect(
#         host=os.getenv('DB_HOST', 'localhost'),
#         port=os.getenv('DB_PORT', '5432'),
#         dbname=os.getenv('CVE_DB_NAME', 'Baseel_CVE'),
#         user=os.getenv('DB_USER', 'postgres'),
#         password=os.getenv('DB_PASSWORD')
#     )
#     cur = conn.cursor()
#     cur.execute("""
#         SELECT table_name 
#         FROM information_schema.tables 
#         WHERE table_schema = 'public'
#     """)
#     tables = cur.fetchall()
#     print("Tables in database:")
#     for table in tables:
#         print(f"- {table[0]}")
        
#     for table in tables:
#         print(f"\nColumns in {table[0]}:")
#         cur.execute(f"""
#             SELECT column_name, data_type 
#             FROM information_schema.columns 
#             WHERE table_name = '{table[0]}'
#         """)
#         columns = cur.fetchall()
#         for col in columns:
#             print(f"  - {col[0]} ({col[1]})")
    
#     # Show iot_info data if table exists
#     try:
#         cur.execute("SELECT COUNT(*) FROM iot_info")
#         count = cur.fetchone()[0]
#         print(f"\n--- iot_info table: {count} records ---")
#         if count > 0:
#             cur.execute("SELECT dataset_name, source, updated_date, data_format FROM iot_info LIMIT 20")
#             rows = cur.fetchall()
#             for i, row in enumerate(rows, 1):
#                 print(f"{i}. {row[0]}")
#                 print(f"   Source: {row[1]}")
#                 if row[2]:
#                     print(f"   Updated: {row[2]}")
#                 if row[3]:
#                     print(f"   Format: {row[3]}")
#     except Exception:
#         print("\niot_info table does not exist yet.")
            
#     cur.close()
#     conn.close()

# if __name__ == "__main__":
#     list_tables()
