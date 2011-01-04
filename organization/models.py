"""An organization is an customer, an install. It can be a company,
a non-profit, a social group (such as a running club), a municipality, etc.
 Each org can have multiple Campaigns, and can brand the site.
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

from django.db import models
from django.core.cache import cache


def org_files_dir(instance, filename):
    """The path to store files for an instance of Organization, 
    relative to MEDIA_ROOT"""
    return 'organization/' + instance.slug + '/' + filename


class OrganizationManager(models.Manager):  # pylint: disable-msg=R0904
    """Methods above the level of a single org"""

    def get_cached(self, domain):
        """The Organization who's domain is 'domain'"""
        cache_key = 'ge_org_map'
        org_map = cache.get(cache_key)

        if not org_map:
            org_map = {}
            for org in Organization.objects.all():
                org_map[org.domain] = org
            cache.set(cache_key, org_map)
            
        try:
            org = org_map[domain]
        except KeyError:
            # Maybe a new org - try loading
            org = self.get(domain=domain)
            org_map[domain] = org
            cache.set(cache_key, org_map)

        return org


class Organization(models.Model):
    """Top level object - has Campaigns, branding, etc"""
    
    objects = OrganizationManager()

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100)
    
    logo = models.ImageField(upload_to=org_files_dir, blank=True, null=True)
    css = models.FileField(upload_to=org_files_dir, blank=True, null=True)

    header_html = models.FileField(
            upload_to=org_files_dir, blank=True, null=True)
    footer_html = models.FileField(
            upload_to=org_files_dir, blank=True, null=True)
    favicon = models.FileField(
            upload_to=org_files_dir, blank=True, null=True)    

    domain = models.CharField(max_length=100)
    home_url = models.CharField(max_length=100, null=True, blank=True)

    def __unicode__(self):
        return self.name

    def has_custom_header(self):
        """Does this organization provide HTML for it's own header?"""
        return self.header_html
 
    def has_custom_footer(self):
        """Does this organization provide HTML for it's own footer?"""
        return self.footer_html

    def header(self):
        """The HTML for this organization's header"""

        header_file = open(self.header_html.path, 'rt')
        html = header_file.read()
        header_file.close()
        return html

    def footer(self):
        """The HTML for this organization's footer"""

        footer_file = open(self.footer_html.path, 'rt')
        html = footer_file.read()
        footer_file.close()
        return html

    def home(self):
        """The URL of companies home page"""
        if self.home_url:
            return self.home_url
        else:
            return '/'

