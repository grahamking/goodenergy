"""A Campaign is what people participate in. Campaign has a start and end date,
and a bunch of Indicators that users track themselves against.
Campaigns belong to Organizations."""

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

import datetime
from json import JSONEncoder

from django.db                  import models
from django.core.cache          import cache
from django.core.urlresolvers   import reverse

from organization.models    import Organization
from profile.models         import Profile
from core.util              import get_current_organization, get_current_user

class CampaignManager(models.Manager):
    'Methods that deal with Campaign objects, above the level of a single object'
    
    def _campaign_cache_key(self, campaign_slug, organization):
        """Key under which to cache the given campaign for this org"""
        return "ge_campaign_%d_%s" % (organization.id, campaign_slug)

    def default(self, campaign_slug, organization):
        """The campaign with slug campaign_slug, or default if not found"""
        
        if not campaign_slug:
            campaign_slug = ''

        cache_key = self._campaign_cache_key(campaign_slug, organization)
        campaign = cache.get(cache_key)
        if not campaign:

            try:
                campaign = self.get(organization = organization, slug = campaign_slug)
            except Campaign.DoesNotExist:

                if self.filter(organization=organization).count() == 1:
                    campaign = self.filter(organization = organization)[0]
                else:
                    raise UserMustSelectCampaign()

                """
                # There should only be one, but just in case use [0]
                try:
                    campaign = self.filter(organization = organization, is_default = True)[0]
                except (IndexError, Campaign.DoesNotExist):
                    # Maybe manager forgot to tick 'Is default'
                    campaign = self.filter(organization = organization)[0]
                """

            cache.set(cache_key, campaign)

        return campaign


def campaign_files_dir(instance, filename):
    'The path to store files for an instance of Campaign, relative to MEDIA_ROOT'
    return 'organization/'+ instance.organization.slug +'/'+ instance.slug +'/'+ filename

class Campaign(models.Model):
    """GoodEnergy is deployed in fixed length campaigns, which contain Indicators to be tracked."""

    objects = CampaignManager()
    
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    organization = models.ForeignKey(Organization)
    is_default = models.BooleanField(default=False)
    
    invite_message = models.CharField(max_length=140, blank=True, null=True)

    login_title = models.CharField(max_length=50, blank=True, null=True)
    join_title = models.CharField(max_length=50, blank=True, null=True)

    login_html = models.TextField(null=True, blank=True)
    join_html = models.TextField(null=True, blank=True)
    promo_html = models.TextField(null=True, blank=True)

    users = models.ManyToManyField(Profile, through='CampaignMembership', null=True, blank=True)
    user_wall = models.ImageField(upload_to=campaign_files_dir, null=True, blank=True,
            help_text='Picture of all the users to display on campaign completed page. '+
                'Use /<campaign_slug>/results/?fresh=1 to get it')

    # Fixed dates True means the campaign runs from start_date to end_date, for everyone.
    # Fixed dates False means the campaign starts the day you join, and runs for a fixed period.
    is_fixed_dates = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name 

    @property
    def users_cache_key(self):
        """Key under which to cache the list of users in this campaign"""
        return 'ge_campaign_users_%d' % self.id

    def add_user(self, geuser):
        """Add a new member to this campaign"""
        if not geuser in self.users.all():
            CampaignMembership.objects.create(campaign = self, user = geuser)
            #self.users.add(geuser)
            cache.delete(self.users_cache_key)
            cache.delete(self._num_users_cache_key)

    @property
    def _num_users_cache_key(self):
        """Key under which to cache the number of users in this campaign"""
        return 'ge_campaign_user_count_%d' % self.id

    def num_users(self):
        'Number of total users in this campaign'
        result = cache.get(self._num_users_cache_key)
        if not result:
            result = self.users.count()
            cache.set(self._num_users_cache_key, result)
        return result

    def view_on_site(self):
        'URL of this campaign, for admin'
        return '<a href="'+ self.get_absolute_url() +'">'+ self.get_absolute_url() +'</a>'
    view_on_site.allow_tags = True  # pylint: disable-msg=W0612
    
    def get_absolute_url(self):
        'Home page of this campaign'
        return '/%s/' % self.slug

    def get_host_register_url(self):
        """Home page of the campaign with full domain name"""
        register = reverse('registration_register', kwargs={'campaign_slug': self.slug})
        return 'http://'+ get_current_organization().domain + register

    def get_refer_url(self):
        """URL for current logged in user to invite others"""
        return "%s?f=%d" % (self.get_host_register_url(), get_current_user().id)

    def get_invite_message(self):
        """The invite message without [url] placeholder"""
        return self.invite_message.replace('[url]', '')

    def active_user_ids(self, cutoff_date=None):
        """Ids of the users (Profile objects) who are active in this campaign.
        @param cutoff_date Users with an answer since this date are considered active. Defaults
        to 30 days ago
        @return A set of the user (Profile) ids who have answered an indicator since cutoff_date.
        """
        from indicator.models import Answer, Indicator

        if not cutoff_date:
            cutoff_date = datetime.date.today() - datetime.timedelta(days=30)

        active_user_ids = set()

        for ind in Indicator.objects.filter(campaign = self):
            ind_user_ids = Answer.objects.\
                    filter(indicator_id = ind.id, action_date__gte = cutoff_date).\
                    values_list('user_id', flat=True)

            active_user_ids.update(ind_user_ids)

        return active_user_ids

    def users_json(self, force=False):
        """JSON array of users in this campaign"""

        result = cache.get(self.users_cache_key)
        if not result or force:
            all_users = self.users.filter(is_system_user=False).select_related(depth=1)
            all_user_maps = [user.as_map() for user in all_users]
            if all_users:
                result = JSONEncoder().encode(all_user_maps)
                cache.set(self.users_cache_key, result)
            else:
                result = "[]"
        return result

    def indicators(self):
        """All the indicators in this campaign. Sub-classes, 
        so IndicatorLikert, IndicatorNumber, etc
        """
        from indicator.models import Indicator
        return Indicator.objects.all_regular_indicators(self)

    def get_start_date(self, geuser):
        """The date this campaign started for geuser"""
        if self.is_fixed_dates:
            return self.start_date
        else:
            membership = CampaignMembership.objects.get(campaign=self, user=geuser)
            return membership.join_date

    def get_end_date(self, geuser):
        """The date this campaign ends for geuser"""
        if self.is_fixed_dates:
            return self.end_date
        else:
            duration = self.end_date - self.start_date
            membership = CampaignMembership.objects.get(campaign=self, user=geuser)
            return membership.join_date + duration

    def stats(self, geuser=None):
        """Overall Campaign stats as a map, with these keys:
            num_users
            num_answers
            answers_per_user
            num_pledges
            num_pledges_completed
            pledges_completed_pct
            num_ideas
        """
        from indicator.models import Answer
        from action.models    import Pledge
        from status.models    import Entry

        if geuser or not hasattr(self, '_stats'):
            stats = {}

            indicator_ids = [ind.id for ind in self.indicator_set.all()]
            answers_qs = Answer.objects.filter(indicator_id__in = indicator_ids)
            if geuser:
                answers_qs = answers_qs.filter(user = geuser)
            num_answers = answers_qs.count()
            stats['num_answers'] = num_answers

            pledge_qs = Pledge.objects.filter(action__campaign = self)
            if geuser:
                pledge_qs = pledge_qs.filter(user = geuser)
            stats['num_pledges'] = num_pledges = pledge_qs.count()

            num_pledges_completed = pledge_qs.filter(is_completed = True).count()
            stats['num_pledges_completed'] = num_pledges_completed

            status_qs = Entry.objects.filter(campaign = self)
            if geuser:
                status_qs = status_qs.filter(who = geuser)
            stats['num_ideas'] = status_qs.count() 

            if geuser:
                return stats

            stats['num_users'] = num_users = self.users.count()
            stats['answers_per_user'] = num_answers / num_users

            if num_pledges:
                stats['pledges_completed_pct'] = num_pledges_completed / float(num_pledges) * 100.0 
            else:
                stats['pledges_completed_pct'] = 0

            self._stats = stats     # pylint: disable-msg=W0201

        return self._stats 

class CampaignMembership(models.Model):
    """Profile joined a Campaign"""

    campaign = models.ForeignKey(Campaign)
    user = models.ForeignKey(Profile)
    join_date = models.DateField(auto_now_add=True)

    def __unicode__(self):
        return '%s joined campaign %s' % (self.user, self.campaign)

class UserMustSelectCampaign(Exception):
    """Thrown when there are several campaigns the user could choose,
    and they haven't specified which"""
    pass

