"""Calculates the daily mean for each indicator. 
The mean is stored as an Answer owned by a special user.
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

import datetime

from django.core.management.base import NoArgsCommand
from django.db.models import Min

from indicator.models import Indicator
from campaign.models import Campaign
from profile.models import Group

class Command(NoArgsCommand):
    'Calculate the daily mean for each indicator'
    
    help = 'Calculate the daily mean for each indicator'
    
    def handle_noargs(self, **options):       # We don't use **options  pylint: disable-msg=W0613
        'Called by NoArgsCommand'
        
        one_day = datetime.timedelta(1)
        average_date = datetime.date.today() - one_day
        end_date = Campaign.objects.aggregate( Min('start_date') )['start_date__min']
        
        average_user = Indicator.objects.average_user()

        try:
            while average_date > end_date:
                print 'Calculating mean for all indicators on %s' % average_date
                
                for campaign in Campaign.objects.all():

                    for indicator in Indicator.objects.all_regular_indicators(campaign):
                        indicator.average(average_date)

                        for group in Group.objects.all():
                            indicator.average(average_date, group=group)
                            Indicator.objects.calculate_day_average(campaign, group.avg_user, average_date)

                    Indicator.objects.calculate_day_average(campaign, average_user, average_date)

                average_date -= one_day

        except Exception:
            import pudb; pudb.post_mortem()
