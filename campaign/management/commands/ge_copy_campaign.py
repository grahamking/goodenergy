"""Copies the contents (indicators and actions) of one campaign into another
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

from django.core.management.base import BaseCommand, CommandError

from profile.models import Profile
from campaign.models import Campaign
from indicator.models import IndicatorLikert, Option
from action.models import Action

def copy_indicators(from_campaign, to_campaign):
    """Copies indicators and options from from_campaign to to_campaign"""

    for indicator in IndicatorLikert.objects.filter(campaign=from_campaign):

        new_indicator, is_created = IndicatorLikert.objects.get_or_create(
                campaign = to_campaign,
                position = indicator.position,
                name = indicator.name,
                question = indicator.question,
                is_synthetic = indicator.is_synthetic,
                description = indicator.description)

        for option in indicator.option_set.all():
            Option.objects.get_or_create(
                    indicator = new_indicator,
                    value = option.value,
                    position = option.position)

        if is_created:
            print('Created indicator %s' % new_indicator)


def copy_actions(from_campaign, to_campaign, action_owner):
    """Copies Actions from from_campaign to to_campaign"""

    for action in from_campaign.action_set.all():

        new_action, is_created = Action.objects.get_or_create(
                campaign = to_campaign,
                title = action.title,
                description = action.description,
                learn_more = action.learn_more,
                created_by = action_owner)
        if is_created:
            print('Created action %s' % new_action)


class Command(BaseCommand):
    """Copies the contents (indicators and actions) of one campaign into another"""
    
    option_list = BaseCommand.option_list
    help = 'Copies the contents (indicators and actions) from one campaign into another'
    args = '<from_campaign_id> <to_campaign_id> <action_owner_username>'
    
    def handle(
            self, 
            from_campaign_id=None, 
            to_campaign_id=None, 
            action_username=None, 
            *args, 
            **options):
        """Main entry point for command"""
        
        if not from_campaign_id or not to_campaign_id or not action_username:
            raise CommandError('Usage is ge_copy_campaign %s' % self.args)

        try:
            from_campaign = Campaign.objects.get(id=from_campaign_id)
        except Campaign.DoesNotExist:
            raise CommandError('FROM Campaign with id %s not found' % from_campaign_id)

        try:
            to_campaign = Campaign.objects.get(id=to_campaign_id)
        except Campaign.DoesNotExist:
            raise CommandError('TO Campaign with id %s not found' % to_campaign_id)

        try:
            action_user = Profile.objects.get(user__username=action_username)
        except Profile.DoesNotExist:
            raise CommandError("Profile for username %s not found" % action_username)

        print('Copying contents of {from_c} into {to_c}.'.\
                format(from_c=from_campaign, to_c = to_campaign))
        confirm = raw_input('Continue? [y|n]')
        if confirm != 'y':
            raise CommandError('Abort')

        copy_indicators(from_campaign, to_campaign)
        copy_actions(from_campaign, to_campaign, action_user)
