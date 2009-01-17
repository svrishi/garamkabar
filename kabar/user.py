from google.appengine.api import users
from google.appengine.ext.db import GqlQuery
from google.appengine.ext import db

from django.http import HttpResponseRedirect

from kabar.models import *

rgsusr_qry_by_usr = GqlQuery(u"SELECT * FROM RegisteredUser \
                        WHERE active = True AND deleted = False AND user = :1")
def get_rgs_user(guser=None, nick=None):
    "Returns registered user object given a user obj or nick, else returns current logged-in user object"
    if nick:
        user_key_name = "user/%s" % nick
        rgs_user = RegisteredUser.get_by_key_name(user_key_name)
        if rgs_user.active and not rgs_user.deleted:
            return rgs_user
        return None
    "Only if no nick given use current user"
    if not guser:
        guser = users.get_current_user()
    if guser:
        global rgsusr_qry_by_usr
        rgsusr_qry_by_usr.bind(guser)
        return rgsusr_qry_by_usr.get()
    return None

def registered_user_required(from_url):
    "decorator to check user login before processing the request"
    def _wrapper(func):
        def _registered_user_required(request):
            user = users.get_current_user()
            if not user:
                return HttpResponseRedirect(users.create_login_url(from_url))

            rgs_user = get_rgs_user(guser=user)
            if not rgs_user:
                return HttpResponseRedirect('/signup?cont=%s' % from_url)
            return func(request)
        return _registered_user_required
    return _wrapper
