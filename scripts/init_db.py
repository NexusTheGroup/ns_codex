"""
Initializes the database schema using a superuser connection.
This script should be run once before the test suite.
"""
import os
from chat_manager.db import ChatDatabase

# Connect as a superuser to create extensions and schema
SUPERUSER_DB_URL = os.environ.get("SUPERUSER_DATABASE_URL", "postgresql://postgres@localhost:5432/test_db")

if __name__ == "__main__":
    print(f"Initializing database from {SUPERUSER_DB_URL}...")
    db = ChatDatabase(dsn=SUPERUSER_DB_URL)

    # Drop and recreate the public schema to ensure a clean slate
    with db.get_cursor(commit=True) as cur:
        print("Dropping and recreating public schema...")
        cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        cur.execute("GRANT ALL ON SCHEMA public TO public;")

    # Initialize the schema from the SQL file
    print("Initializing schema from docs/DB_SCHEMA.sql...")
    db.initialize(schema_path="docs/DB_SCHEMA.sql")

    print("Database initialized successfully.")
    db.close()
