from google.appengine.ext import db

from kabar.models import *
from kabar.vote import rank_fn
from kabar.controller import clear_posts_cache

import logging

def update_source(src, ckey, rank):
    src.num_comments += 1
    src.ckeylist.append(ckey)
    src.ranklist.append(rank)
    src.clist.append(str(ckey))
    src.put()

def post_comment(src, ruser, text):
    c=Comment(posted_by_ruser=ruser,src=src,text=text,parent=src)
    c.rank = rank_fn(c.created_on, c.points)
    if c.put():
        update_source(src, c.key(), c.rank)
    clear_posts_cache()

def update_comment(c, text):
    c.text = text
    c.put()

def post_reply(cmnt, ruser, text):
    src = cmnt.src
    reply=Comment(posted_by_ruser=ruser,src=src,text=text,parent=cmnt)
    reply.rank = rank_fn(reply.created_on, reply.points)
    reply.depth = cmnt.depth + 1
    if reply.put():
        update_source(src, reply.key(), reply.rank)
    clear_posts_cache()

def get_comments(src):
    clist = []
    if not src:
        return None
    for c in src.ckeylist:
        clist.append(db.get(c))
    return clist
