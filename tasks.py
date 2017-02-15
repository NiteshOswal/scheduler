from __future__ import absolute_import
from celery import Celery

# user defined modules
from config import celery

tq = Celery()
tq.config_from_object(celery)
print tq.conf.humanize(with_defaults=False, censored=True)

@tq.task(name="analytics.add", bind=True)
def add(self, x, y):
    print self
    print dir(self)
    return x+y