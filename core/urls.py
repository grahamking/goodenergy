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

from django.conf.urls.defaults      import patterns, url
from django.views.generic.simple    import direct_to_template

from core.views import dashboard, contact, results
from core.util import chop_campaign
from indicator.views import redirect_to_indicator

urlpatterns = patterns('',

    url(r'^contact/$', contact, name='contact'),
    url(r'^contact/thanks/$', chop_campaign(direct_to_template), {'template': 'contact_thanks.html'}),
    
    url(r'^feedback/$', contact, {'success_url': '/home/', 'title': 'Feedback'}),

    url(r'^results/$', results, name='results'),
    url(r'^results/(?P<indicator_id>[\d]+)/$', results, name='results_specific'),

    url(r'^(?P<indicator_id>\d+)/$', dashboard, name='indicator_home'),
    url(r'^$', redirect_to_indicator, name='campaign_home'),
)
