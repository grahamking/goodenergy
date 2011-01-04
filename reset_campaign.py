#!/usr/bin/python
""" Deletes all Answers, Status updates, and Comments. Resets the start date
of the campaign to today.
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

import sys
import datetime

from django.db import connection

from campaign.models import Campaign
from indicator.models import Answer, Indicator
from status.models import Entry
from action.models import Pledge, Barrier

def delete_answers(campaign):
    """Delete the Answers to Indicators from this campaign"""
    indicator_ids = Indicator.objects.filter(campaign = campaign).values_list('id', flat=True)
    answers = Answer.objects.filter(indicator_id__in = indicator_ids)

    print('Deleting %d answers' % answers.count())
    connection.queries = []
    answers.delete()
    print( _pretty_queries(connection.queries) )

def delete_entries(campaign):
    """Delete the status updates and their comments from this campaign"""
    entries = list( Entry.objects.filter(campaign = campaign) )

    connection.queries = []
    print('Deleting %d status updates' % len(entries))
    for entry in entries:
        entry.entrycomment_set.all().delete()
        entry.delete()
    print( _pretty_queries(connection.queries) )

def reset_campaign(campaign):
    """Set the start date of the campaign to today, and end date to in six weeks.
    Removes all the users from this campaign."""

    print('Reseting start / end dates')
    now = datetime.datetime.now()
    six_weeks_hence = now + datetime.timedelta(7 * 6)
    campaign.start_date = now
    campaign.end_date = six_weeks_hence

    connection.queries = []
    campaign.save()
    print( _pretty_queries(connection.queries) )

    print('Resetting user points')
    for user in campaign.users.all():
        user.participation_points = 1
        user.inspiration_points = 1
        user.inspiration_points_credit = 1
        user.save()

    print('Unlinking %d users' % campaign.users.count())
    campaign.users.clear()

def delete_pledges(campaign):
    """Delete the Pledges and Barriers on Actions"""
    pledges = Pledge.objects.filter(action__campaign = campaign)
    print('Deleting %d pledges' % pledges.count())
    connection.queries = []
    pledges.delete()
    print( _pretty_queries(connection.queries) )

    barriers = Barrier.objects.filter(action__campaign = campaign)
    print('Deleting %d barriers' % barriers.count())
    connection.queries = []
    barriers.delete()
    print( _pretty_queries(connection.queries) )

def reset(campaign):
    """Resets a campaign"""

    delete_answers(campaign)
    delete_entries(campaign)
    delete_pledges(campaign)

    reset_campaign(campaign)

    print('Reset complete')

def _pretty_queries(query_map):
    """Takes django's connection.queries and return just the queries one per line"""
    queries = [entry['sql'] for entry in query_map]
    return '\n'.join(queries)

def main():
    'Start!'

    if len(sys.argv) != 2:
        print('Usage: reset_campaign <campaign_name>')
        return

    name = sys.argv[1]
    try:
        campaign = Campaign.objects.get(name=name)
    except Campaign.DoesNotExist:
        print('No campaign called "%s"' % name)
        return

    reset(campaign)

if __name__ == '__main__':
    main()
