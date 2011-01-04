"""Models that don't fit anywhere else, and not big enough to warrant their own app"""

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
# pylint: disable-msg=R0904

from django.db import models
from django.conf import settings

from core.baseconv import base62

class ShortURLManager(models.Manager):
    """Methods above the level of ShortURL"""

    def make(self, url):
        """Creates, saves and returns an absolute short url which will redirect 
        to the given url.
        """

        short, _ = self.get_or_create(url = url)
        return settings.SHORT_URL_DOMAIN + str(base62.from_decimal(short.id))

    def resolve(self, short_url):
        """Takes a short url and returns the real full one"""
        if short_url.endswith('/'):
            short_url = short_url[:-1]

        try:
            code = short_url.split('/')[-1]
            short_id = base62.to_decimal(code)
            return self.get(pk = short_id).url
        except Exception:
            raise ShortURL.DoesNotExist('No short url for %s' % short_url)


class ShortURL(models.Model):
    """A Short url for micro-blogging services"""

    objects = ShortURLManager()

    url = models.URLField(unique=True)

    def __unicode__(self):
        return self.url

