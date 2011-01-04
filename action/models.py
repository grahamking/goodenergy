"""Business objects for Action
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

# Django manager have many public methods
# pylint: disable-msg=R0904

from django.db import models
from django.core.cache import cache

from campaign.models import Campaign
from profile.models import Profile
from status.models import Entry
from status.view_objects import EntryView

class ActionManager(models.Manager):
    """Methods above the level of  a single Action"""

    def popular(self, campaign, limit=10):
        """Most popular actions in this campaign.
        @param limit How many items to return.
        """
        action_list = self.filter(campaign = campaign)[:limit]
        return action_list

    def dashboard_cache_key(self, campaign, geuser):
        """Key to cache the rendered dashboard for actions"""
        return 'ge_action_%d_%d' % (campaign.id, geuser.id)

    def clear_dashboard_cache(self, campaign):
        """Clear the cache for actions"""
        # TODO: Should be done by the worker
        for geuser in campaign.users.all():
            cache.delete( self.dashboard_cache_key(campaign, geuser) )

class Action(models.Model):
    """An action that users can pledge to do, then actually do.

    Examples:
    - Write to the Prime Minister.
    - Cycle to work for a week
    """

    objects = ActionManager()

    campaign = models.ForeignKey(Campaign)

    title = models.CharField(max_length = 250)
    description = models.TextField()
    learn_more = models.TextField(null=True, blank=True)

    # created_by allows nulls so the user who created it can be deleted without deleting the Action
    created_by = models.ForeignKey(Profile, null=True)
    created = models.DateTimeField(auto_now_add=True)

    comment_count = models.IntegerField(default=0)

    def __unicode__(self):
        return self.title

    def pledge(self, geuser):
        """geuser pledges to perform this action.
        Records the Pledge, posts a message to community feed, and clears relevant caches"""

        _, is_created = Pledge.objects.get_or_create(action = self, user = geuser)

        if is_created:
            entry = Entry(who = geuser,
                          msg = 'pledged to <strong>%s</strong>' % self.title,
                          campaign = self.campaign)
            entry.save()
            EntryView.refresh_recent_activity(self.campaign)
            Entry.objects.clear_dashboard_cache(self.campaign)

        Action.objects.clear_dashboard_cache(self.campaign)

    def pledge_count(self, user_ids=None):
        """Pledges to do this action, whether completed or not
        @param user_ids: Narrow to these users
        """
        query_set = Pledge.objects.filter(action=self)
        if user_ids:
            query_set = query_set.filter(user__id__in = user_ids)
        return query_set.count()

    def open_pledge_count(self):
        """Uncompleted pledges"""
        return Pledge.objects.filter(action=self, is_completed=False).count()

    def completed_count(self, user_ids=None):
        """Completed pledges
        @param user_ids: Narrow to these users
        """
        query_set = Pledge.objects.filter(action=self, is_completed=True)
        if user_ids:
            query_set = query_set.filter(user__id__in = user_ids)
        return query_set.count()

    def recent_pledges(self, limit=5):
        """Recent pledges to complete this action"""
        return self.pledge_set.select_related(depth=1).order_by('-created')[:limit]

    def update_comment_count(self):
        'Recalculates the value of comment_count. Saves if the value has changed'
        self._update_count('comment_set', 'comment_count')

    def _update_count(self, attr_name, count_attr_name):
        'Update a database cached count'

        new_count = getattr(self, attr_name).count()
        current_count = getattr(self, count_attr_name)

        if new_count != current_count:
            setattr(self, count_attr_name, new_count)
            self.save()


class Pledge(models.Model):
    """User commits to doing a given action"""

    user = models.ForeignKey(Profile)
    action = models.ForeignKey(Action)

    is_completed = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)

class Comment(models.Model):
    """A comment on an Action"""
    
    action = models.ForeignKey(Action)
    user = models.ForeignKey(Profile, related_name='action_comment_set')
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """Django configuration"""
        ordering = ('created',)
    
    def __unicode__(self):
        return self.comment

    def as_map(self):
        'This Comment as a map - good for serializing'
        return {
                'id': self.id,
                'user_id': self.user_id,
                'comment': self.comment,
                'created': self.created
                }


class Barrier(models.Model):
    """Something that prevents someone from completing an action"""

    action = models.ForeignKey(Action)
    title = models.CharField(max_length = 250)
    description = models.TextField(null=True, blank=True)

    users = models.ManyToManyField(Profile, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title

