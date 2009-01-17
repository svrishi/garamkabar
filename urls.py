# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *

urlpatterns = patterns('kabar.views',
    # Example:
    # (r'^foo/', include('foo.urls')),
      url(r'^$', 'index', name="home_page"),
      url(r'^page/(?P<page>\d{1,2})/$', 'index', name="top_posts"),
      url(r'^latest/$', 'index', name="latest_home_page"),
      url(r'^latest/page/(?P<page>\d{1,2})/$', 'index', {'latest':'1'}, "new_posts"),
      url(r'^post/$', 'post'),
      url(r'^signup/$', 'signup'),
      url(r'^about/$', 'about'),
      url(r'^user/(\w{1,35})/$', 'user_profile'),
      url(r'^source/(?P<srcid>\d{1,30})/$', 'source'),
      url(r'^comment/(?P<commentkey>\w{1,90})/$', 'comment'),
    # Uncomment this for admin:
    # (r'^admin/', include('django.contrib.admin.urls')),
)

urlpatterns += patterns('kabar.vote',
      (r'^vote/up/$', 'voteup'),
      (r'^vote/down/$', 'votedown'),
)
