import logging
import random
from datetime import datetime

from google.appengine.ext.db import GqlQuery
from google.appengine.ext import db

from kabar.models import *

def GetCount(counter_type): 
    result = 0
    for rec in Counter.gql('WHERE type=:1', counter_type):
        result += rec.value
    return result

last_counter_update = {}
def IncCounter(counter_type):
    counter_id = 'ctr/%s/%s' % (counter_type, random.randint(1, Counter.RECSPERTYPE))
    def update():
        rec = Counter.get_by_key_name(counter_id)
        if rec:
            value = rec.value + 1
            rec.count = value
        else:
            value = 1
            rec = Counter(key_name=counter_id, type=counter_type, value=value)
        if not db.put(rec):
            return 0
        return value
    def updatehistory():
        global last_counter_update
        lastupdate = last_counter_update.get(counter_type, None)
        now = datetime.utcnow()
        if lastupdate:
            diff = now - lastupdate
        if not lastupdate or diff.days > 0:
            last_counter_update[counter_type] = now
            hrec = CounterHistory(type=counter_type, datetime=now, value=value)
            hrec.put()
        return True
    value = db.run_in_transaction(update)
    if not value:
        logging.error("Error incrementing counter for user %s", str(ruser.user))
        return
    if not db.run_in_transaction(updatehistory):
        logging.error("Error incrementing counter in history for user %s", str(ruser.user))
