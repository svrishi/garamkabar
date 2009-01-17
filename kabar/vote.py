import string
import logging
from math import fabs, log10
from datetime import datetime

from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.db import GqlQuery
from google.appengine.api import memcache

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.utils.html import escape

from kabar.models import *
from kabar.user import get_rgs_user
from kabar.counter import IncCounter

def ajax_resp(rc=0, id='',value=''):
    data = { 'retcode':rc, 'id':id, 'value':value }
    json = simplejson.dumps(data)
    resp = HttpResponse(json, mimetype="application/json")
    return resp

def update_user_karma(ruser_id, delta):
    ruser = RegisteredUser.get_by_key_name(ruser_id)
    if not ruser:
        return False
    ruser.karma += delta
    if db.put(ruser):
        return True
    return False

def vote_tx(src, ruser_id, delta):
    if ruser_id in src.voted_users:
        return None
    src.points += delta
    src.voted_users.append(ruser_id)
    if delta > 0:
        src.upvoted_users.append(ruser_id)
        src.upvotes += 1
    else:
        src.downvoted_users.append(ruser_id)
        src.downvotes += 1
    src.rank = rank_fn(src.created_on, src.points)
    if src.put():
        return src.points
    return None

def do_vote(ruser, src_id, delta):
    src = Source.get(src_id)
    if not src:
        return None
    ruser_id = ruser.entry_id()
    if ruser_id in src.voted_users:
        return None
    src_user_id = src.posted_by_ruser.entry_id()
    if ruser_id == src_user_id:
        return None
    val = db.run_in_transaction(vote_tx, src, ruser_id, delta) 
    if val:
        memcache.delete("top_posts")
        memcache.delete("new_posts")
        if delta > 0:
            IncCounter(Counter.UVOTES)
        else:
            IncCounter(Counter.DVOTES)
        db.run_in_transaction(update_user_karma, src_user_id, delta)
        return val
    return None

def voteup(request):
    if request.method == 'POST':
        ruser = get_rgs_user()
        if not ruser:
            return ajax_resp(1)
        id = string.strip(escape(request.POST.get('id','')))
        idarr = string.split(id,'voteup')
        if not len(id) or len(idarr) != 2:
            return ajax_resp()
        val = do_vote(ruser, idarr[1], 1)
        if not val:
            return ajax_resp()
        return ajax_resp(2, idarr[1], val)
    else:
        return HttpResponse('You must have Javascript disabled else please report this error.')

def votedown(request):
    if request.method == 'POST':
        ruser = get_rgs_user()
        if not ruser:
            return ajax_resp(1)
        id = string.strip(escape(request.POST.get('id','')))
        idarr = string.split(id,'votedown')
        if not len(id) or len(idarr) != 2:
            return ajax_resp()
        val = do_vote(ruser, idarr[1], -1)
        if not val:
            return ajax_resp()
        return ajax_resp(2, idarr[1], val)
    else:
        return HttpResponse('You must have Javascript disabled else please report this error.')

"""
Credits: http://redflavor.com/reddit.cf.algorithm.png
"""
epoch = datetime(2008, 07, 01, 0, 0, 0)
def rank_fn(post_date, points):
    time_diff = post_date - epoch
    age = time_diff.seconds + (time_diff.days*24*60*60.0)
    sign = 1 if points > 0 else -1
    rpoints = fabs(points) if points >= 1 else 1
    rank = log10(rpoints) + ((sign*age)/45000.0)
    return rank
