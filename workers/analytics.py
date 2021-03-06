from __future__ import absolute_import
import json
import sys, os
from celery import Celery
import psycopg2


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import postgres

# we need config in our path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import celery as celery_config

# configure celery
app = Celery()
app.config_from_object(celery_config)

@app.task(name='analytics.issue_token', bind=True)
def issue_token(self, payload):
    conn = psycopg2.connect(
        dbname=postgres.database,
        user=postgres.username,
        password=postgres.password,
        host=postgres.host,
        port=postgres.port
    )
    try:
        if type(payload) == list:
            payload = tuple(payload)
        token_cursor = conn.cursor()
        token_cursor.execute("SELECT token FROM tokens WHERE token = '%s' LIMIT 1" % (payload[0]))
        token = token_cursor.fetchone()
        if not token:
            token_cursor.execute("INSERT INTO tokens (token, origin, user_agent, ip, extra) VALUES ('%s', '%s', '%s', '%s', '%s')" % payload)
        token_cursor.close()
        conn.commit() # commit to the db
    except psycopg2.ProgrammingError, e:
        self.retry(exc=e, countdown=1)
    except Exception, e:
        self.retry(exc=e, countdown=1)
    conn.close();

@app.task(name='analytics.identify', bind=True)
def identify(self, token, identify):
    conn = psycopg2.connect(
        dbname=postgres.database,
        user=postgres.username,
        password=postgres.password,
        host=postgres.host,
        port=postgres.port
    )
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tokens SET profile = '%s' WHERE token = '%s'
        """ % (
            json.dumps(identify).replace("'", "''"),
            token
        ))
        conn.commit()
        cursor.close()
    except psycopg2.ProgrammingError, e:
        self.retry(exc=e, countdown=1)
    except Exception, e:
        self.retry(exc=e, countdown=1)
    conn.close()

# define tasks
@app.task(name='analytics.pool', bind=True)
def pool(self, token, event):
    conn = psycopg2.connect(
        dbname=postgres.database,
        user=postgres.username,
        password=postgres.password,
        host=postgres.host,
        port=postgres.port
    )
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO analytics_dump (token, data) VALUES ('%s', '%s')
        """ % (
            token,
            json.dumps(event).replace("'", "''")
        ))
        conn.commit()
        cursor.close()
    except psycopg2.ProgrammingError, e:
        self.retry(exc=e, countdown=1)
    except Exception, e:
        self.retry(exc=e, countdown=1)
    conn.close()
    return True