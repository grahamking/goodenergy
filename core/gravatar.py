"""Makes gravatar url for given email address"""

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


import urllib

from django.conf import settings
from django.utils.hashcompat import md5_constructor
from django.utils.html import escape

GRAVATAR_URL_PREFIX = getattr(settings, "GRAVATAR_URL_PREFIX", "http://www.gravatar.com/")
GRAVATAR_DEFAULT_IMAGE = getattr(settings, "GRAVATAR_DEFAULT_IMAGE", "")
GRAVATAR_DEFAULT_SIZE = 40

def for_email(email, size=80):
    "Copied from http://code.google.com/p/django-gravatar"
    url = "%savatar/%s/?" % (GRAVATAR_URL_PREFIX, md5_constructor(email).hexdigest())
    #url += urllib.urlencode({"s": str(size), "default": GRAVATAR_DEFAULT_IMAGE})
    url += urllib.urlencode({"s": str(size), "default": "404"})
    return escape(url)
