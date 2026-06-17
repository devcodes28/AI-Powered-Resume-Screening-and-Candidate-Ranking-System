import psycopg2
import sys

def get_db_connection():
    try:
        from config import Config
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"\nCRITICAL DATABASE CONNECTION ERROR: {e}", file=sys.stderr)
        return None

def execute_query(query, params=(), fetch=False):
    conn = get_db_connection()
    if not conn:
        return None
    result = None
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                result = cursor.fetchall()
            conn.commit()
    except Exception as e:
        print(f"Database Query Error: {e}", file=sys.stderr)
        conn.rollback()
    finally:
        if conn:
            conn.close()
    return result

def init_db():
    print("[DEBUG] Attempting to connect to ShaktiDB...", flush=True)
    conn = get_db_connection()
    if conn is None:
        print("[DEBUG] Connection failed. Exiting initialization pipeline.", flush=True)
        return
    try:
        print("[DEBUG] Connection verified. Reading schema.sql...", flush=True)
        with open('database/schema.sql', 'r') as f:
            schema_sql = f.read()
        with conn.cursor() as cursor:
            print("[DEBUG] Executing SQL Schema strings...", flush=True)
            cursor.execute(schema_sql)
        conn.commit()
        print("[+] ShaktiDB initialized successfully with schema structures.", flush=True)
    except Exception as e:
        print(f"\nCRITICAL SCHEMA EXECUTION ERROR: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()
