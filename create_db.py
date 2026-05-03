import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    print("Connecting to postgres to create taskmanager database...")
    # Connect to the default 'postgres' db first
    conn = psycopg2.connect(
        user="postgres",
        password="Admin@123",
        host="localhost",
        port="5432",
        database="postgres"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'taskmanager'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("CREATE DATABASE taskmanager")
        print("Successfully created database 'taskmanager'!")
    else:
        print("Database 'taskmanager' already exists.")
        
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
