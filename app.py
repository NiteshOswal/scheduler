# -*- coding: utf-8 -*-
import sys
import os
import flask
import json
import uuid
import psycopg2
import psycopg2.extras
import arrow
import math
from flask_cors import CORS, cross_origin

sys.path.append(os.path.dirname(os.path.abspath(__file__))) #add this path so the module dependencies work nicely..
# from workers import instance
from config import postgres
from workers import analytics as analytics_worker
from workers import social as social_worker

conn = psycopg2.connect(
    dbname=postgres.database,
    user=postgres.username,
    password=postgres.password,
    host=postgres.host,
    port=postgres.port
)

webapp = flask.Flask(__name__)
CORS(webapp)

def get_ip(obj):
    print obj
    keys = [
        'HTTP-CLIENT-IP',
        'HTTP-X-FORWARDED-FOR',
        'HTTP-X-FORWARDED',
        'HTTP-X-CLUSTER-CLIENT-IP',
        'HTTP-FORWARDED-FOR',
        'HTTP-FORWARDED'
    ]
    for key, value in obj.iteritems():
        if key in keys:
            return value
    return False

@webapp.route('/')
def ping():
    return flask.jsonify({"ping": "pong"})

@webapp.route('/token', methods=['GET'])
def issue_token():
    ip = get_ip(flask.request.headers)
    token_seeder = {
        "user_agent": flask.request.headers['user-agent'],
        "ip": flask.request.remote_addr if not ip else ip
    }
    token_seed = filter(lambda x: ord(x) <= 127, ("%(ip)s|%(user_agent)s" % token_seeder).encode('utf8')) # just don't want any weird values in there
    token = uuid.uuid3(uuid.NAMESPACE_OID, token_seed)
    payload = (
        token,
        flask.request.args['origin'] if 'origin' in flask.request.args else "",
        token_seeder['user_agent'],
        token_seeder['ip'],
        json.dumps({
            "headers": dict(flask.request.headers),
            "args": dict(flask.request.values),
            "form": dict(flask.request.form),
            "is_xhr": flask.request.is_xhr
        })
    )
    signature = analytics_worker.issue_token.delay(payload=payload) # should be the next thing up your mind, yes queue
    return flask.jsonify({
        "s": token_seed,
        "u": token
    })

@webapp.route('/identify', methods=['POST'])
def identify():
    if not flask.request.data:
        return flask.jsonify(0)
    data = json.loads(flask.request.data)
    signature = analytics_worker.identify.signature((flask.request.args['token'], data), countdown=5)
    signature.delay()
    return flask.jsonify(1)

@webapp.route('/analytics', methods=['POST'])
def analytics_pool():
    if not flask.request.data:
        return flask.jsonify(0)
    data = json.loads(flask.request.data)
    signature = analytics_worker.pool.signature((flask.request.args['token'], data), countdown=5)
    signature.delay()
    return flask.jsonify(1)

@webapp.route('/schedule', methods=['POST'])
def social_pool():
    payload = flask.request.get_json()
    if "date" in payload and "action" in payload:
        seconds = math.ceil((arrow.get(payload['date']) - arrow.utcnow()).total_seconds())
        task = social_worker.pool.s(payload).apply_async(countdown=seconds)
        return flask.jsonify({
            "status": True,
            "payload": payload,
            "scheduled_seconds": seconds,
            "task": task.id
        })
    else:
        return flask.jsonify({
            "status": False,
            "error": "Date or Action is not present."
        })

