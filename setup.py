import sys
import os
import psycopg2
import psycopg2.extras

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# from workers import instance
from config import postgres

conn = psycopg2.connect(
    dbname=postgres.database,
    user=postgres.username,
    password=postgres.password,
    host=postgres.host,
    port=postgres.port
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cursor.execute("""
    CREATE TABLE tokens (
        token UUID PRIMARY KEY,
        origin TEXT,
        user_agent TEXT,
        ip INET, 
        extra JSON,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")
cursor.execute("""
    CREATE TABLE analytics_dump (
        token UUID,
        data JSON
    )
""")
conn.commit()
cursor.close()
conn.close()