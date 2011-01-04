"""Various utility functions"""

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


import threading
import datetime
import calendar
import pytz

from django.template import defaultfilters
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.http import urlquote
from django.http import HttpResponseRedirect
from django.conf import settings

_thread_local = threading.local()    # IGNORE:C0103

def clear_current_user():
    'Remove the user, call this on logout'
    try:
        del _thread_local.user
    except AttributeError:          # IGNORE:W0704
        pass

def set_current_user(user):
    'Record the current user'
    _thread_local.user = user

def set_current_organization(org):
    'Record the current organisation'
    _thread_local.org = org

def set_current_campaign(campaign):
    """Record the current campaign"""
    _thread_local.campaign = campaign

def get_current_user():
    'The user who is currently logged in - instance of Profile'
    try:
        return _thread_local.user
    except AttributeError:
        return None

def get_current_organization():
    'The current organization - instance of Organization'
    try:
        return _thread_local.org
    except AttributeError:
        return None

def get_current_campaign():
    """The current campaign - instance of Campaign"""
    try:
        return _thread_local.campaign
    except AttributeError:
        return None

def slugify(name, max_len=50):
    'A short link friendly version of name, truncated to max_len characters'
    long_slug = defaultfilters.slugify(name)
    return long_slug if len(long_slug) <= max_len else long_slug[:max_len]

def redirect(request, response):
    'Tweaks a response to work with Ajax calls.'

    if request.is_ajax() and response.status_code == 302:
        response.status_code = 278 # Custom error code indicating a user handled redirect

    return response

def json_encoder_default(obj):
    """"Serialize datetime and date to JSON, returns time in milliseconds
    start of epoch (1970-01-01 00:00:00 UTC).
    In practice this means we are assuming the given time is also UTC.
    Graphing library flot.js needs all its dates in UTC.
    """
    if isinstance(obj, datetime.date):
        obj = datetime.datetime.combine(obj, datetime.time())

    if isinstance(obj, datetime.datetime):
        return calendar.timegm( pytz.utc.localize(obj).timetuple() ) * 1000

'''
def json_encoder_utc(obj):
    """Serialize datetime and date to JSON as RFC822 datetime"""
    if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        return obj.strftime("%a, %d %b %Y %H:%M:%S %z") 
'''

class DummyRequest():
    "Can be passed to a view method as the 'request' param - used by the management commands"

    def __init__(self, user, post):

        self.user = user
        self.method = 'POST'
        self.POST = post

def unique_field(starter, django_class, fieldname):
    'Generate a unique value for the given class and field'

    field, _, _, _ = django_class._meta.get_field_by_name(fieldname)
    max_length = field.max_length

    candidate = starter[:max_length]
    num = None
    while 1:
    
        try:
            django_class.objects.get( **{fieldname: candidate} )
        except MultipleObjectsReturned:
            pass
        except ObjectDoesNotExist:
            return candidate

        if not num:
            num = 0
        num += 1
        s_num = str(num)

        if (len(starter) + len(s_num) + 1) > max_length:
            starter = starter[: max_length - len(s_num) - 1 ]

        candidate = starter +'-'+ s_num

def chop_campaign(function):
    """Decorator to remove the campaign_slug param from the call string.
    The campaign is available from core.util.get_current_campaign."""
    def _inner(*args, **kwargs):
        'Wrapper'
        if 'campaign_slug' in kwargs:
            del kwargs['campaign_slug']
        return function(*args, **kwargs)
    return _inner

def ge_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """Decorator to add campaign slug to login url, replaces django's login_required"""

    def _inner(request, *args, **kwargs):
        'Wrapper'
        if not request.user.is_authenticated():
            path = urlquote(request.get_full_path())
            login_url = '/'+ get_current_campaign().slug + settings.LOGIN_URL
            tup = login_url, redirect_field_name, path
            return HttpResponseRedirect('%s?%s=%s' % tup)
        return function(request, *args, **kwargs)

    return _inner

