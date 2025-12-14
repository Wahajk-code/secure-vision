import psycopg2
from config import DB_CONFIG

def verify_connection():
    print(f"Connecting to DB: {DB_CONFIG['dbname']} at {DB_CONFIG['host']}...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connection Successful!")
        
        # Create Table if verification passes
        create_table_query = """
        CREATE TABLE IF NOT EXISTS security_events (
            id SERIAL PRIMARY KEY,
            timestamp FLOAT,
            datetime TIMESTAMP,
            event_type VARCHAR(50),
            details JSONB,
            stream_id VARCHAR(100)
        );
        """
        cur = conn.cursor()
        cur.execute(create_table_query)
        conn.commit()
        print("✅ Table 'security_events' ensured.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    verify_connection()
