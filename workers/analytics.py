from __future__ import absolute_import
import json
import sys, os
from celery import Celery
import psycopg2


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import postgres

conn = psycopg2.connect(
    dbname=postgres.database,
    user=postgres.username,
    password=postgres.password,
    host=postgres.host,
    port=postgres.port
)

# we need config in our path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import celery as celery_config

# configure celery
app = Celery()
app.config_from_object(celery_config)

@app.task(name='analytics.issue_token', bind=True)
def issue_token(self, payload):
    token_cursor = conn.cursor()
    token_cursor.execute("SELECT token FROM tokens WHERE token = '%s' LIMIT 1" % (payload[0]))
    token = token_cursor.fetchone()
    if not token:
        token_cursor.execute("INSERT INTO tokens (token, origin, user_agent, ip, extra) VALUES ('%s', '%s', '%s', '%s', '%s')" % payload)
    token_cursor.close()
    conn.commit() # commit to the db

# define tasks
@app.task(name='analytics.pool', bind=True)
def pool(self, token, event):
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO analytics_dump (token, data) VALUES ('%s', '%s')
    """ % (
        token,
        json.dumps(event)
    ))
    conn.commit()
    cursor.close()
    return True