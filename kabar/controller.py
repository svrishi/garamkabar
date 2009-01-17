import logging
import re
from datetime import datetime
from urlparse import urlparse

from google.appengine.api import users
from google.appengine.ext.db import GqlQuery
from google.appengine.ext import db
from google.appengine.api import memcache

from django.forms.fields import email_re
from django.conf import settings

from kabar.models import *
from kabar.counter import IncCounter
from kabar.user import get_rgs_user
from kabar.vote import rank_fn

# Global defaults
POST_RETCODE_MSGS = (
	u'Thank you, your submission has been posted.',
    u'Title and URL are required fields.',
    u'Title is too short/long.',
    u'URL is too short/long.',
    u'Invalid URL, please ensure URL is of the form: http://hname.tld/path/to/page',
    u'Duplicate submission, this post was previously submitted',
    u'Invalid email, please enter a valid email address (less than 100 chars)',
    u'Invalid nickname, please enter a valid nickname (only letters, nums and underscores, 5-35 chars)',
    u'Nickname and/or email address is in use by another user.',
    u'Error in peforming a store in the database, an error has been logged.'
)

class ReturnCode:
    "Return codes, when adding a new return code do increase the range!"
    OK, EREQ, ETITLELEN, EURLLEN, EINVALURL, EDUPSRC, \
    EINVALEMAIL, EINVALNICK, EDUPUSR, ESTORE, EMAX = range(11)

class Limits:
    MAXEMAILLEN = 50
    MINTITLELEN = 5
    MAXTITLELEN = 80
    MINURLLEN = 5
    MAXURLLEN = 250
    MINNICKLEN = 4
    MAXNICKLEN = 35
    MAXPAGES = 4
    MAXDISPPOSTS = 150 
    MAXPOSTSPERPAGE = 15 

def get_error_str(retcode):
    "Returns error string given the return code"
    try: retcode = int(retcode)
    except: return ''
    if retcode >= ReturnCode.OK or retcode < ReturnCode.EMAX:
        return POST_RETCODE_MSGS[retcode]
    return ''

def create_new_user(nick, email, user):
    user_key_name = "user/%s" % nick
    rgs_user = RegisteredUser.get_by_key_name(user_key_name)
    if not rgs_user:
        rgs_user = RegisteredUser(key_name=user_key_name,nick=nick,email=email,user=user)
        if settings.DEBUG and nick.startswith("sadmin"):
            rgs_user.is_admin = True
        else:
            rgs_user.is_admin = users.is_current_user_admin()
        if not rgs_user.put():
            return None
        return rgs_user
    return None

dup_user_by_nick = GqlQuery(u"SELECT * FROM RegisteredUser WHERE nick = :1")

dup_user_by_guser = GqlQuery(u"SELECT * FROM RegisteredUser WHERE \
                             Active = True AND deleted = False AND user = :1")
dup_user_by_email = GqlQuery(u"SELECT * FROM RegisteredUser WHERE \
                             Active = True AND deleted = False AND email = :1")
def new_user(nick, email, user, results):
    "Create new user after verifying the user attributes"
    global dup_user_by_nick
    global dup_user_by_guser
    global dup_user_by_email
    if len(nick) < Limits.MINNICKLEN  or len(nick) >= Limits.MAXNICKLEN:
        results['retcode'] = ReturnCode.EINVALNICK
        return False
    if len(email) == 0 or len(email) >= Limits.MAXEMAILLEN:
        results['retcode'] = ReturnCode.EINVALEMAIL
        return False
    alnum_re = re.compile(r'^\w+$')
    if not alnum_re.search(nick):
        results['retcode'] = ReturnCode.EINVALNICK
        return False
    if not email_re.search(email):
        results['retcode'] = ReturnCode.EINVALEMAIL
        return False
    dup_user_by_guser.bind(user)
    if dup_user_by_guser.count(1) > 0:
        results['retcode'] = ReturnCode.EDUPUSR
        return False
    dup_user_by_email.bind(email)
    if dup_user_by_email.count(1) > 0:
        results['retcode'] = ReturnCode.EDUPUSR
        return False
    dup_user_by_nick.bind(nick)
    if dup_user_by_nick.count(1) > 0:
        results['retcode'] = ReturnCode.EDUPUSR
        return False
    q = db.run_in_transaction(create_new_user, nick, email, user)
    if not q:
        results['retcode'] = ReturnCode.EDUPUSR
        return False
    IncCounter(Counter.REGUSERS)
    return True

def verify_post(title, url, results):
    "Verify new post submission attributes"
    if len(title) == 0 or len(url) == 0:
        results['errcode'] = ReturnCode.EREQ
        return False
    if len(title) > Limits.MAXTITLELEN or len(title) < Limits.MINTITLELEN:
        results['errcode'] = ReturnCode.ETITLELEN
        return False
    if len(url) > Limits.MAXURLLEN or len(url) < Limits.MINURLLEN:
        results['errcode'] = ReturnCode.EURLLEN
        return False
    parsed_url = good_url(url)
    if not parsed_url:
        results['errcode'] = ReturnCode.EINVALURL
        return False
    results['parsed_url'] = parsed_url
    return True

def good_url(url):
    "check if the URL looks good"
    o = urlparse(url, 'http')
    if o.scheme != 'http' or len(o.netloc) == 0 or  \
        (not o.hostname) or (o.hostname and len(o.hostname) == 0) \
        or o.username or o.password or o.port:
        return None
    # TODO: should check for spaces
    return o

dup_post_qry = GqlQuery(u"SELECT * FROM Source WHERE active = True AND \
                       deleted = False AND hostname = :1 AND urlpath = :2")
def dup_post(hname, path):
    "check if the post is a duplicate"
    global dup_post_qry
    dup_post_qry.bind(hname, path)
    if dup_post_qry.count(1) > 0:
        return True
    return False

def track_user_post(user_key, src_key_id):
    ruser = RegisteredUser.get_by_key_name(user_key)
    if not src_key_id in ruser.submissions:
        ruser.submissions.append(src_key_id)
        ruser.num_posts += 1
        ruser.last_post_date = datetime.utcnow()
        ruser.karma += 1 
        if db.put(ruser):
            return True
    return False

def submit_post(title, url, ruser):
    "Submit a new post after verifying the post details"
    results = {}
    if not verify_post(title, url, results):
        return results['errcode']

    purl = results['parsed_url']
    hostname = purl.hostname
    if hostname.startswith(u'www.'):
        hostname = hostname[4:]
    urlpath = purl.path
    if urlpath == u'/':
        urlpath = u''

    if dup_post(hostname, urlpath):
        return ReturnCode.EDUPSRC
    src = Source(url=url, title=title, 
                 hostname=hostname,
                 posted_by_ruser=ruser,
                 urlpath=urlpath)
    src.rank = rank_fn(src.created_on, src.points)
    if not db.put(src):
        return ReturnCode.ESTORE
    if not db.run_in_transaction(track_user_post, ruser.entry_id(),
                                 src.entry_id()):
        return ReturnCode.ESTORE
    IncCounter(Counter.SRCS)
    clear_posts_cache
    return ReturnCode.OK

def get_page_info(pagenum):
    try:
        page = int(pagenum)
        if not (page > 0 and page < Limits.MAXPAGES):
            page = 0
    except: page = 0
    if not page:
        return (0, 0)
    offset = Limits.MAXPOSTSPERPAGE*(page-1) + 1
    return (page, offset)
 
top_posts_qry = GqlQuery(u"SELECT * FROM Source WHERE active = True AND \
                       deleted = False ORDER BY rank DESC, created_on DESC")
new_posts_qry = GqlQuery(u"SELECT * FROM Source WHERE active = True AND \
                       deleted = False ORDER BY created_on DESC")
def get_disp_posts(page, offset, latest=False): 
    "Returns the top posts for display" 
    if not page or not offset:
        return None
    mckey = "new_posts" if latest else "top_posts"
    posts = memcache.get(mckey)
    if posts:
        return posts[offset-1:Limits.MAXPOSTSPERPAGE+1]
    if latest:
        global new_psts_qry
        posts = new_posts_qry.fetch(Limits.MAXDISPPOSTS)
    else:
        global top_posts_qry
        posts = top_posts_qry.fetch(Limits.MAXDISPPOSTS)
    if not posts:
        return None
    memcache.set(mckey, posts)
    return posts[offset-1:Limits.MAXPOSTSPERPAGE+1]

def clear_posts_cache():
    memcache.delete("top_posts")
    memcache.delete("new_posts")
