import logging
import string

from google.appengine.api import users
from google.appengine.api import memcache

from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.html import escape
from django.conf import settings
from django.core.urlresolvers import reverse

from kabar.models import *
from kabar.user import get_rgs_user
from kabar.user import registered_user_required
from kabar.controller import Limits
from kabar.controller import new_user
from kabar.controller import submit_post
from kabar.controller import get_disp_posts
from kabar.controller import get_page_info
from kabar.controller import get_error_str
from kabar.controller import POST_RETCODE_MSGS
from kabar.comments import *

# Global Defaults
login_url = users.create_login_url('/signup')
logout_url = users.create_logout_url('/')

def signup(request):
    "Handles signup requests. If user already registered, re-direct to main page"
    user = users.get_current_user()
    if not user:
        return HttpResponseRedirect(login_url)
    if get_rgs_user(guser=user):
        return HttpResponseRedirect('/')

    if request.method == 'POST':
        results = {}
        nick = string.lower(escape(string.strip(request.POST.get('nick',''))))
        email = string.lower(escape(string.strip(request.POST.get('email',''))))
        if not new_user(nick=nick, email=email, user=user, results=results):
             return HttpResponseRedirect('/signup?rc=%d' % results['retcode'])
        return HttpResponseRedirect(request.POST.get('cont','/'))
    elif request.method == 'GET':
        error_str = get_error_str(escape(request.GET.get('rc', '')))
        return render_to_response('signup.html', 
                                  {'user_nick':user.nickname(), 
                                   'user_email':user.email(), 
                                   'error_str':error_str,
                                   'cont':request.GET.get("cont", "/"), 
                                   'act':request.GET.get("act",""), 
                                   'actarg':request.GET.get("actarg",""), 
                                  }, context_instance=RequestContext(request))
    return HttpResponseRedirect('/')

def index(request, page='1', latest='0'):
    "Handles main/index page request"
    if request.method == 'GET':
        page, offset = get_page_info(page)
        posts = get_disp_posts(page, offset, (latest=='1'))
        more_pages = (posts and len(posts) == Limits.MAXPOSTSPERPAGE and not page > Limits.MAXPAGES)
        mcache_stats = memcache.get_stats() if settings.DEBUG else None
        return render_to_response('index.html', 
                                  {'ruser':get_rgs_user(),
                                   'login_url':login_url,
                                   'logout_url':logout_url,
                                   'page':page, 'offset':offset,
                                   'disp_posts': posts,
                                   'latest':latest=='1', 'more_pages': more_pages,
                                   'mcache_stats': mcache_stats,
                                  }, context_instance=RequestContext(request))
    return HttpResponseRedirect('/')

def about(request):
    if request.method == 'GET':
        return render_to_response('about.html',
                                  {'ruser':get_rgs_user(),
                                   'login_url':login_url,
                                   'logout_url':logout_url,
                                  }, context_instance=RequestContext(request))
    return HttpResponseRedirect('/')

@registered_user_required('/post/')
def post(request):
    "Handles post/source submission requests"
    ruser = get_rgs_user()
    if request.method == 'GET':
        error_str = get_error_str(escape(request.GET.get('rc', '')))
        return render_to_response('post.html',
                                   {
                                    'ruser' : ruser,
                                    'logout_url':logout_url,
                                    'error_str':error_str,
                                   },
                                  context_instance=RequestContext(request))
    elif request.method == 'POST':
        title = string.strip(escape(request.POST.get('title','')))
        url = string.lower(string.strip(escape(request.POST.get('url',''))))
        retcode = submit_post(title=title, url=url, ruser=ruser)
        return HttpResponseRedirect('/post?rc=%d' % retcode)
    return HttpResponseRedirect('/')

def user_profile(request, nick):
    if nick and request.method == 'GET':
        nick = string.lower(escape(string.strip(nick)))
        ruser = get_rgs_user()
        puser = get_rgs_user(nick=nick)
        is_owner = (ruser and ruser.nick == nick)
        if puser:
            return render_to_response('profile.html', 
                                  {'ruser':ruser,
                                   'puser':puser,
                                   'login_url':login_url,
                                   'is_owner':is_owner,
                                   'logout_url':logout_url,
                                  }, context_instance=RequestContext(request))
    elif nick and request.method == 'POST':
        ruser = get_rgs_user()
        if ruser and nick == ruser.nick:
            pass
    return HttpResponseRedirect('/')

def source(request, srcid):
    "Handles source page request"
    try: srcid=long(srcid)
    except: src = None
    else: src = Source.get_by_id(srcid)
    if not src:
        return HttpResponseRedirect('/')

    ruser = get_rgs_user()
    if request.method == 'POST':
        if not ruser:
            return HttpResponseRedirect('/')
        text=escape(string.strip(request.POST.get('ctext','')))
        if len(text) > 0:
            post_comment(src, ruser, text)

    return render_to_response('source.html', 
                          {'ruser':ruser,
                           'login_url':login_url,
                           'logout_url':logout_url,
                           'src': src,
                           'comments':get_comments(src),
                          }, context_instance=RequestContext(request))

def comment(request, commentkey):
    "Handles comment page requests to Reply and Edit"
    cmnt = Comment.get(db.Key(commentkey))
    if not cmnt:
        return HttpResponseRedirect('/')
    ruser = get_rgs_user()
    if request.method == 'GET':
        return render_to_response('comment.html', 
                          {'ruser':ruser,
                           'login_url':login_url,
                           'logout_url':logout_url,
                           'comment': cmnt,
                          }, context_instance=RequestContext(request))
    # Post new/edit comment
    if not ruser:
        return HttpResponseRedirect('/')
    text=escape(string.strip(request.POST.get('ctext','')))
    if len(text) > 0:
        if ruser.entry_id() == cmnt.posted_by_ruser.entry_id():
            update_comment(cmnt, text)
        else:
            post_reply(cmnt, ruser, text)
    # Re-direct to source page
    return HttpResponseRedirect(reverse("kabar.views.source",
                                        args=[str(cmnt.src.entry_id())]))

