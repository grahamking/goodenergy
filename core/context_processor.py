"""Template context processor"""

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

from django.conf import settings

from core.util import get_current_user, get_current_organization, get_current_campaign

def context(request):
    'Custom template_context_processor. Adds context for template pages'

    result = {}
    result['geuser'] = geuser = get_current_user()
    result['organization'] = get_current_organization()

    result['campaign'] = campaign = get_current_campaign()
    if request.user.is_authenticated() and geuser and campaign:
        campaign.add_user(geuser)
        result['campaign_start_date'] = campaign.get_start_date(geuser)
        result['campaign_end_date'] = campaign.get_end_date(geuser)

    result['MEDIA_1'] = settings.MEDIA_URL_1
    result['MEDIA_2'] = settings.MEDIA_URL_2
    return result
