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
from profile.views import profile_settings, crop, invite
from profile.views import about, detail, give_inspiration_point
from profile.views import users_csv, is_email_registered, gravatar_url

urlpatterns = patterns('',

    url(r'^is_email/$', is_email_registered, name='is_email_registered'),
    url(r'^gravatar/$', gravatar_url, name='gravatar_url'),

    url(r'^settings/$', profile_settings, name='profile_settings'),
    url(r'^invite/$', invite, name='profile_invite'),

    #url(r'^search/$', search, name='profile_search'),

    url(r'^crop/$', crop, name='profile_crop'),
    url(r'^about/$', about, name='profile_about'),

    # All the users in current users Organization, as CSV
    url(r'^all.csv$', users_csv, name='users_csv'),

    url(r'^gip/(?P<user_id>\d+)/', give_inspiration_point, name='give_inspiration_point'),

    url(r'^(?P<username>[\w|\_|\-]+)/', detail, name='detail'),
)
