"""View objects for status package
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


from django.core.cache import cache
from django.conf import settings

from status.models import Entry

class EntryView(object):
    'View representation of an Entry'

    RECENT_ACTIVITY_KEY = 'ge_recent_activity_%d'

    @staticmethod
    def recent_activity(campaign, force=False):
        """Recent status updates"""

        cache_key = EntryView.RECENT_ACTIVITY_KEY % campaign.id
        recent_activity = cache.get(cache_key)
        if not recent_activity or force:
            recent_activity = [EntryView(entry) for entry in Entry.objects.recent_activity(campaign)]
            cache.set(cache_key, recent_activity)
        return recent_activity

    @staticmethod
    def refresh_recent_activity(campaign):
        """Refresh cached recent activity"""
        EntryView.recent_activity(campaign, force=True)

    def __init__(self, entry):
        self.id = entry.id
        self.when = entry.when
        self.as_html = entry.as_html()
        self.comment_count = entry.comment_count

        owner = entry.who.get_profile()
        self.owner_id = owner.id
        self.owner_url = owner.get_absolute_url()
        self.owner_thumb = owner.thumb_url()
        self.owner_name = unicode(owner)

        liked_by = list( entry.liked_by.all() )
        self.i_like = owner in liked_by
        self.is_liked = len(liked_by) > 0
        self.others_who_like = liked_by
        if self.i_like:
            self.others_who_like.remove(owner)

        self.all_comments = entry.entrycomment_set.all()

