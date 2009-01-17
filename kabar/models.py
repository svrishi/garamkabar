from appengine_django.models import BaseModel
from google.appengine.ext import db

class RegisteredUser(BaseModel):
    """
    A Google Accounts user with our site preferences

    # Create some Registered Users
    >>> u=RegisteredUser(nick="test",email="test@test.org")
    >>> u.nick
    'test'
    >>> u.email
    u'test@test.org'
    >>> u.karma
    1
    >>> u.registered_date != None
    True
    >>> u.last_update_date != None
    True
    >>> u.num_posts
    0
    >>> u.active
    True
    >>> u.is_admin
    False
    >>> u.deleted
    False
    >>> u.submissions
    []
    """
    nick = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)
    num_posts = db.IntegerProperty(default=0)
    karma = db.IntegerProperty(default=1)
    registered_date = db.DateTimeProperty('date registered', auto_now_add=True)
    last_update_date = db.DateTimeProperty('date last updated', auto_now=True)
    last_post_date = db.DateTimeProperty('date last posted')
    is_admin = db.BooleanProperty(default=False)
    active = db.BooleanProperty(default=True)
    inactive_date = db.DateTimeProperty()
    deleted = db.BooleanProperty(default=False)
    deleted_date = db.DateTimeProperty()
    user = db.UserProperty()
    about_page_url = db.StringProperty(default="")
    about_me = db.TextProperty(default="")
    model_version = db.IntegerProperty(default=0)
    # List of sources posted
    submissions = db.ListProperty(long,default=None)

    # Returns a unique string ID based on unique nick
    def entry_id(self):
        return self.key().name()
    # Returns a unique display ID (string representation of key object)
    def disp_id(self):
        return str(self.key())

class Source(BaseModel):
    """
    Source posted by a registered user

    # Create a new source

    >>> s=Source(title="Test",url="http://test.org")
    >>> s.created_on != None
    True
    >>> s.points
    1
    >>> s.active
    True
    >>> s.deleted
    False
    """
    url = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    uuid = db.StringProperty()
    hostname = db.StringProperty()
    urlpath = db.StringProperty()
    created_on = db.DateTimeProperty('date source posted', auto_now_add=True)
    # status
    active = db.BooleanProperty(default=True)
    inactive_date = db.DateTimeProperty()
    deleted = db.BooleanProperty(default=False)
    deleted_date = db.DateTimeProperty()
    posted_by_ruser = db.ReferenceProperty(RegisteredUser)
    disqus_url = db.StringProperty()
    model_version = db.IntegerProperty(default=0)
    # voting
    points = db.IntegerProperty(default=1)
    rank = db.FloatProperty(default=0.0)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    # List of users voted
    voted_users = db.StringListProperty(default=None)
    upvoted_users = db.StringListProperty(default=None)
    downvoted_users = db.StringListProperty(default=None)
    # Comments
    num_comments = db.IntegerProperty(default=0)
    clist = db.StringListProperty()
    ranklist = db.ListProperty(float)
    ckeylist = db.ListProperty(db.Key)
    
    # Returns a unique long integer ID
    def entry_id(self):
        return self.key().id()
    # Returns a unique display ID (string representation of key object)
    def disp_id(self):
        return str(self.key())

class Comment(BaseModel):
    depth = db.IntegerProperty(default=0)
    path = db.StringProperty()
    #
    src = db.ReferenceProperty(Source,required=True)
    text = db.TextProperty(required=True)
    created_on = db.DateTimeProperty('date comment created', auto_now_add=True)
    last_touched = db.DateTimeProperty('date comment updated/voted', auto_now=True)
    # status
    active = db.BooleanProperty(default=True)
    inactive_date = db.DateTimeProperty()
    deleted = db.BooleanProperty(default=False)
    deleted_date = db.DateTimeProperty()
    posted_by_ruser = db.ReferenceProperty(RegisteredUser, required=True)
    # voting
    points = db.IntegerProperty(default=1)
    rank = db.FloatProperty(default=0.0)
    upvotes = db.IntegerProperty(default=0)
    downvotes = db.IntegerProperty(default=0)
    # List of users voted
    voted_users = db.StringListProperty(default=None)
    upvoted_users = db.StringListProperty(default=None)
    downvoted_users = db.StringListProperty(default=None)
    # Returns a unique long integer ID
    def entry_id(self):
        return self.key().id()
    # Returns a unique display ID (string representation of key object)
    def disp_id(self):
        return str(self.key())

class Counter(BaseModel):
    SRCS, INACTSRCS, DELSRCS, UVOTES, DVOTES, \
      REGUSERS, INACTREGUSRES, DELUSERS = range(8)
    RECSPERTYPE = 10
    type = db.IntegerProperty(required=True)
    value = db.IntegerProperty(default=0)

class CounterHistory(BaseModel):
    type = db.IntegerProperty(required=True)
    datetime = db.DateTimeProperty(required=True)
    value = db.IntegerProperty(default=0)
