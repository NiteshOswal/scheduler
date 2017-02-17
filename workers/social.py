from __future__ import absolute_import
import json
import sys, os
from celery import Celery
from requests import Request, Session

# we need config in our path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import celery as celery_config

# configure celery
app = Celery()
app.config_from_object(celery_config)

@app.task(name='social.pool', bind=True)
def pool(self, payload):
    rd = {
        "method": "GET",
        "url": "local.apps",
        "body": {},
        "headers": {}
    }
    try:
        if type(payload) == type(""):
            payload = json.loads(payload) # make sure the payload always an object
        if type(payload) == type({}):
            rd.update(payload['action'])
            session = Session()
            request = Request(rd['method'], rd['url'], data=rd['body'], headers=rd['headers'])
            prepped = request.prepare()
            r = session.send(prepped)
            return r.text
    except Exception, e:
        return json.dumps({"status": False, "uuid": self.request.id, "error": str(e)})
