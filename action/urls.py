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

from action.views import pledge, done, full, create
from action.views import search, barriers, user_actions

urlpatterns = patterns('',
  
  url(r'^pledge/(?P<action_id>\d+)/$', pledge, name='action_pledge'),
  url(r'^done/(?P<action_id>\d+)/$', done, name='action_done'),
  url(r'^full/(?P<action_id>\d+)/$', full, name='action_full'),
  url(r'^create/$', create, name='action_create'),

  url(r'^(?P<action_id>\d+)/barriers/$', barriers, name='action_barriers'),

  url(r'^search/$', search, name='action_search'),
  url(r'^(?P<username>[\w|_|-]+)/$', user_actions, name='user_actions'),

 ) 
