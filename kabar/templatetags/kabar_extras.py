from django import template
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse

register = template.Library()

@register.filter
def nickurlize(ruser, showkarma):
    nurl = reverse('kabar.views.user_profile', args=[ruser.nick])
    if showkarma == 1:
        result = '<a href="%s">%s(%s)</a>' % (nurl, ruser.nick, ruser.karma)
    else:
        result = '<a href="%s">%s</a>' % (nurl, ruser.nick)
    return mark_safe(result)

@register.filter
def usercanvote(ruser, src):
    if not ruser:
        # No user logged-in case
        return True
    if not src:
        # should never happen
        return False
    return not ((ruser.entry_id() in src.voted_users)
        or (src.posted_by_ruser.entry_id() == ruser.entry_id()))
usercanvote.is_safe = True
