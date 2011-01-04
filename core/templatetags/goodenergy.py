"""Good Energy template tags"""

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


from django import template

from core.util import get_current_user

register = template.Library()

@register.filter("js_utc")
def js_utc(dt):
    """Takes a datetime and returns a string like Date.UTC(1976, 07, 27).
    This makes a Python datetime intelligible to Javascript, especially flot
    """
    # Remember that in JS, the month is 0 based, so subtract 1 from month
    return 'Date.UTC(%s, %s, %s)' % (dt.year, dt.month - 1, dt.day)

def ge_admin_list_filter(cl, spec):
    "Extends django.contrib.admin's admin_list_filter"

    org = get_current_user().organization
    campaign_tuple = [(campaign.id, campaign.name) 
            for campaign in org.campaign_set.all().order_by('name')]
    spec.lookup_choices = campaign_tuple

    return {'title': spec.title(), 'choices' : list(spec.choices(cl))}
ge_admin_list_filter = register.inclusion_tag('admin/filter.html')(ge_admin_list_filter)

