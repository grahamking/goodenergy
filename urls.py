""" Mapping of URLs to methods. Start here to understand the project
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


from django.contrib               import admin
from django.conf.urls.defaults    import patterns, url, include
from django.contrib.auth.views    import password_reset_done
from django.views.generic.simple  import direct_to_template
from django.conf                  import settings

# In order for the 404 and 500 default views to work, we need this line:
from django.conf.urls.defaults  import handler404, handler500

from profile.views import register, login, logout_then_login
from profile.views import password_reset, password_reset_confirm, \
                            password_reset_complete
from campaign.views import redirect_to_default
from core.util import chop_campaign
from core import manager  # Creates manager.SITE as an AdminSite

admin.autodiscover()

# Admin
# -----
urlpatterns = patterns('',
    #(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^manager/', include(manager.SITE.urls)),
)

# Apps
# ----
urlpatterns += patterns('',

    url(r'^select/$', direct_to_template, {'template': 'campaign/list.html'}, 
        name='select_campaign'),

    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/register/$', 
        register, name='registration_register'),
    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/login/$', 
        login, name='auth_login'),
    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/logout/$', 
        logout_then_login, name='registration_logout'),

    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/password/reset/$', 
        password_reset, name='password_reset'),

    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/password/reset/done/$', 
        chop_campaign(password_reset_done), name='password_reset_done'),

    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/password/reset/confirm/$', 
        chop_campaign(password_reset_done), name='password_reset_done'),

    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 
        password_reset_confirm, name='password_reset_confirm'),

    url(r'^(?P<campaign_slug>[\w|-|_]+)/accounts/password/reset/complete/$', 
        password_reset_complete, name='password_reset_complete'),

    (r'^(?P<campaign_slug>[\w|-|_]+)/actions/', include('action.urls')),
    (r'^(?P<campaign_slug>[\w|-|_]+)/status/', include('status.urls')),
    (r'^(?P<campaign_slug>[\w|-|_]+)/indicators/', include('indicator.urls')),
    (r'^(?P<campaign_slug>[\w|-|_]+)/users/', include('profile.urls')),
    (r'^(?P<campaign_slug>[\w|-|_]+)/campaigns/', include('campaign.urls')),
    
    (r'^(?P<campaign_slug>[\w|-|_]+)/', include('core.urls')),

    # Development 
    # -----------
    (r'^media/(?P<path>.*)$', 
        'django.views.static.serve', 
        {'document_root': settings.MEDIA_ROOT}),

    # No campaign slug in url, redirect to default
    (r'', redirect_to_default),
)
