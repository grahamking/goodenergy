""" Mapping of URLs to methods for this app
"""

#    Copyright 2010,2011 Good Energy Research Inc. <graham@goodenergy.ca>, <jeremy@goodenergy.ca>
#    
#    This file is part of Good Energy.
#    
#    Good Energy is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    
#    Good Energy is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#    
#    You should have received a copy of the GNU Affero General Public License
#    along with Good Energy. If not, see <http://www.gnu.org/licenses/>.
#


# Disable the pylint check for dynamically added attributes. This happens a lot
# with Django DB model usage.
# pylint: disable-msg=E1101
# pylint: disable-msg=E1103

from django.conf.urls.defaults  import patterns, url

from status.views import create, activity_like, activity_unlike, clear_cache
from status.views import comment, user_activity, comment_delete, next_activity

urlpatterns = patterns('',  
  url(r'^add/$', create, name='status_post'),
  url(r'(?P<object_id>\d+)/like/$', activity_like, name='activity_like'),
  url(r'(?P<object_id>\d+)/unlike/$', activity_unlike, name='activity_unlike'),
  url(r'(?P<object_id>\d+)/comment/$', comment, name='activity_comment'),
  url(r'(?P<object_id>\d+)/comment/delete/$', comment_delete, name='activity_comment_delete'),

  url(r'clear_cache/$', clear_cache, name='activity_clear_cache'),

  url(r'^user_activity/$', user_activity, name='user_activity'),
  url(r'^next_activity/$', next_activity, name='next_activity'),
)
