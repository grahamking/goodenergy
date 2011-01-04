"""Middleware"""

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
# pylint: disable-msg=E1101,E1103,R0903,R0201

import sys

from django.core.urlresolvers import reverse
from django.core.exceptions import MiddlewareNotUsed
from django.db import connection
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse

from core.util import set_current_user, clear_current_user, \
        set_current_organization
from core.util import set_current_campaign
from core.models import ShortURL
from profile.models import Profile
from organization.models import Organization
from campaign.models import Campaign, UserMustSelectCampaign


class UserMiddleware:
    'Get the user from the request and records it on a threadlocal'
    
    def __init__(self):
        pass
    
    def process_request(self, request):
        'Runs before views.py'
                
        if settings.MEDIA_URL in request.path:
            return
        
        if request.user.is_anonymous():
            clear_current_user()
            return
 
        try:
            user = Profile.objects.get_cached_by_auth_userid(request.user.id)
            set_current_user(user)
            # Monkey patch to save a database query
            request.user.get_profile = lambda: user
        except Profile.DoesNotExist:
            # Super-users, for example, don't need a profile
            return


class OrganizationMiddleware:
    """
    - Redirect any shortened urls
    - Get the organisation off the url and record it on a threadlocal
    - Get the campaign off the url and record it on a threadlocal
    """
    
    def __init__(self):
        pass
    
    def process_request(self, request):
        """Runs before views.py"""

        if settings.MEDIA_URL in request.path or '/admin' in request.path:
            return

        absolute = 'http://%s/' % request.get_host()
        if absolute == settings.SHORT_URL_DOMAIN:
            try:
                short = ShortURL.objects.resolve(request.path)
                return HttpResponseRedirect(short)
            except ShortURL.DoesNotExist:
                pass

        domain = request.get_host()
        if ':' in domain:
            domain = domain.split(':')[0]

        try:
            org = Organization.objects.get_cached(domain)
        except Organization.DoesNotExist:

            try:
                org = Organization.objects.all()[0]
            except Organization.DoesNotExist:
                return HttpResponse('No organizations found. ' +
                                    'Create one via /admin/',
                            mimetype='text/plain')
 
        set_current_organization(org)

        try:
            campaign_name = request.path.split('/')[1]
        except IndexError:
            campaign_name = ''

        if campaign_name != 'select':   # select is url to select a campaign
            try:
                campaign = Campaign.objects.default(campaign_name, org)
                set_current_campaign(campaign)
            except UserMustSelectCampaign:
                return HttpResponseRedirect(reverse('select_campaign'))


class RefererMiddleware:
    """Records in a cookie which user referer this user.
    That cookie is checked when a user registers.
    Register can't just check the url, beause there could be some redirects
    between first arrival and actual registration."""

    def __init__(self):
        pass

    def process_response(self, request, response):
        """Runs after views.py"""
        if settings.MEDIA_URL in request.path:
            return response

        if 'f' in request.GET:
            response.set_cookie('f', request.GET['f'])
        return response


class SqlStatementCountMiddleware:
    'Prints out a count of the number of SQL statements that were run'

    def __init__(self):
        if not settings.DEBUG:
            raise MiddlewareNotUsed()

    def process_response(self, request, response):
        'Runs once the work is done, prints out sql statement count'

        if settings.MEDIA_URL in request.path:
            return response

        num_queries = len(connection.queries)
        if num_queries:
            # No using 'print', it appends a \n
            sys.stdout.write('SQL %d\t' % num_queries)
            sys.stdout.flush()

        return response
