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

from indicator.views import answer_create_single, answer_table, questions_json
from indicator.views import create_edit, indicator_list, delete, indicators_csv, answers_csv

urlpatterns = patterns('',
  
  url(r'^input/(?P<indicator_id>\d+)/$', answer_create_single, name='single_input_with_id'),
  url(r'^input/$', answer_create_single, name='single_input'),
  
  url(r'^questions.json$', questions_json, name='questions_json'),
  url(r'^all.csv$', indicators_csv, name='indicators_csv'),
  url(r'^answers.csv$', answers_csv, name='answers_csv'),

  #url(r'^(?P<campaign_slug>[\w|\_|\-]+)/answers.json$', answers_json, name='answers_json'),
  
  # Admin
  url(r'^indicators/(?P<campaign_id>\d+)/$', indicator_list, name='indicator_list'),
  url(r'^create/(?P<campaign_id>\d+)/$', create_edit, name='indicator_create'),
  url(r'^edit/(?P<indicator_id>\d+)/$', create_edit, name='indicator_edit'),
  url(r'^delete/(?P<indicator_id>\d+)/$', delete, name='indicator_delete'),

  # For debugging
  url(r'^data/(?P<user_id>\d+)/$', answer_table, name='answer_table')
)
