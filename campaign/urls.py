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

from campaign.views import create_edit, delete, users, users_json, campaigns_csv

urlpatterns = patterns('',
  
  url(r'^create/$', create_edit, name='campaign_create'),
  url(r'^edit/(?P<campaign_id>\d+)/', create_edit, name='campaign_edit'),
  url(r'^delete/(?P<campaign_id>\d+)/', delete, name='campaign_delete'),
  url(r'^users/(?P<campaign_id>\d+)/', users, name='campaign_active_users'),

  url(r'^users/all.json', users_json, name='campaign_users_json'),

  url(r'^all.csv', campaigns_csv, name='campaigns_csv'),

)

