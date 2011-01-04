"""View objects which wrap model objects
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

import operator

from django.conf import settings
from django.core.cache import cache

from action.models import Pledge, Action

class ActionView(object):
    """View of an Action"""

    @staticmethod
    def _popular_action_key(campaign_id, geuser_id):
        """Cache key for popular actions for this user in this campaign"""
        return 'ge_popular_actions_%d_%d' % (campaign_id, geuser_id)

    @staticmethod
    def _popular_action_index_key(campaign_id):
        """Cache key for the array of user ids who have cached popular actions"""
        return 'ge_popular_actions_index_%d' % campaign_id

    @staticmethod
    def popular(campaign, geuser, force=False):
        """Popular actions in this campaign current user hasn't completed yet"""

        cache_key = ActionView._popular_action_key(campaign.id, geuser.id) 
        result = cache.get(cache_key)

        if not result or force:
            actions = Action.objects.popular(campaign)
            action_views = [ActionView(action, geuser) for action in actions]
            action_views.sort(key = operator.attrgetter('open_and_completed'), reverse=True)
            result = [action for action in action_views if not action.is_completed]
            cache.set(cache_key, result)

            index_cache_key = ActionView._popular_action_index_key(campaign.id)
            index = cache.get(index_cache_key, [])
            if not geuser.id in index:
                index.append(geuser.id)
                cache.set(index_cache_key, index)

        return result

    @staticmethod
    def clear_popular_cache(campaign):
        """Delete the cached popular actions for this campaign."""
        index_cache_key = ActionView._popular_action_index_key(campaign.id)
        index = cache.get(index_cache_key)

        if index:
            cache.delete(index_cache_key)

            keys_to_delete = []
            for geuser_id in index:
                keys_to_delete.append( ActionView._popular_action_key(campaign.id, geuser_id) )

            cache.delete_many(keys_to_delete)

    def __init__(self, action, user=None):

        self.id = action.id
        self.title = action.title
        self.description = action.description
        self.learn_more = action.learn_more

        try:
            if not user:
                raise Pledge.DoesNotExist()
            pledge = Pledge.objects.get(action=action, user=user)
            self.is_pledged = True
            self.is_completed = pledge.is_completed
        except Pledge.DoesNotExist:
            self.is_pledged = False
            self.is_completed = False

        self.open_pledge_count = action.open_pledge_count()
        self.completed_count = action.completed_count()

        self.total_pledges = self.open_pledge_count + self.completed_count

        # If I did it, the counts reflect other people ('You and x other people..')
        if self.is_pledged and not self.is_completed:
            self.open_pledge_count -= 1
        elif self.is_completed:
            self.completed_count -= 1

        self.open_and_completed = self.open_pledge_count + self.completed_count

        self.barriers = [BarrierView(b, user) for b in action.barrier_set.all()]
        self.barrier_count = len(self.barriers)

        creator = action.created_by
        self.created_by_id = creator.id
        self.created_by = unicode(creator)
        self.created_by_url = creator.get_absolute_url()
        self.created_by_thumbnail = creator.thumb_url()


    def __unicode__(self):
        return self.title

    def __str__(self):
        return unicode(self)

class BarrierView(object):
    """View of a Barrier"""

    def __init__(self, barrier, user=None):

        self.id = barrier.id
        self.title = barrier.title
        self.user_count = barrier.users.count()

        self.i_have = False
        if user:
            self.i_have = user in barrier.users.all()

    def __unicode__(self):
        return self.title

    def __str__(self):
        return unicode(self)

