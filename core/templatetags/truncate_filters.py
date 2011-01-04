"""Modified version of: http://w.holeso.me/2008/08/a-simple-django-truncate-filter/"""

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
register = template.Library()

@register.filter("truncate_chars")
def truncate_chars(value, max_length):
    if len(value) > max_length:
        truncd_val = value[:max_length]
        if not len(value) == max_length+1 and value[max_length+1] != " ":
            truncd_val = truncd_val[:truncd_val.rfind(" ")]
        return  truncd_val + "..."
    return value
