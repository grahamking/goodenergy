""" Facebook / Twitter style status updates
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
from django.template.defaultfilters import urlize

from profile.models import Profile
from campaign.models import Campaign


class EntryManager(models.Manager):
    'Methods above the level of a single Entry'

    def recent_activity(self, campaign, start=0):
        'Recent activity in this campaign'
        return list( self.filter(campaign = campaign).select_related(depth=2)[start:start+10] )

    def dashboard_cache_key(self, campaign, geuser):
        """Key to cache the rendered dashboard for status updates"""
        return 'ge_status_%d_%d' % (campaign.id, geuser.id)

    def clear_dashboard_cache(self, campaign):
        """Clear the cache for status updates"""
        # TODO: Should be done by the worker
        for geuser in campaign.users.all():
            cache.delete( self.dashboard_cache_key(campaign, geuser) )

class Entry(models.Model):
    'A post / tweet / message in the micro blog'

    objects = EntryManager()

    who = models.ForeignKey(Profile)
    when = models.DateTimeField(auto_now_add=True)
    msg = models.CharField(max_length=250)
    campaign = models.ForeignKey(Campaign)

    liked_by = models.ManyToManyField(Profile, null=True, blank=True, related_name='liked_entries')

    comment_count = models.IntegerField(default=0)

    class Meta:
        """Django config"""
        ordering = ['-when']
        verbose_name_plural = 'entries'

    def __unicode__(self):
        return '(%d) %s: %s' % (self.id,  unicode(self.who), self.msg)

    def as_html(self):
        """HTML rendering of this entry"""
        return '<span class="activity_feed_object">%s</span>' % urlize(self.msg)

    def update_comment_count(self):
        'Recalculate how many comments this entry has. Saves if the number of comments has changed'
        new_count = self.entrycomment_set.count()
        if new_count != self.comment_count:
            self.comment_count = new_count
            self.save()

    def others_who_like(self):
        'Users who like this, not including the current user'
        from core.util import get_current_user
        current_user = get_current_user()
        return [user for user in self.liked_by.all() if user != current_user]

    def as_map(self):
        'This activity as a map - used to create JSON'
        
        result = {}
        result['id'] = self.id
        result['who_id'] = self.who.id
        result['when'] = self.when
        result['actionHTML'] = self.as_html()
        result['comments'] = [comment.as_map() for comment in self.entrycomment_set.all()]
        result['likes'] = [profile.as_map() for profile in self.liked_by.all()]
        
        return result


class EntryComment(models.Model):
    'Comment on an activity'

    user = models.ForeignKey(Profile)
    created = models.DateTimeField(auto_now_add=True)
    entry = models.ForeignKey(Entry)
    comment = models.TextField()

    class Meta:
        """Django config"""
        ordering = ('created',)
    
    def __unicode__(self):
        return unicode(self.id)

    def as_map(self):
        'This comment as a map'
        return {'comment': self.comment, 
                'created': self.created, 
                'user': self.user.as_map()}
