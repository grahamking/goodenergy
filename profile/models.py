""" Profile is Good Energy specific user data.
Get from Django's auth.User via user.get_profile()
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


# pylint: disable-msg=E1101,E1103,R0904,R0201

import datetime
from json import JSONEncoder

from django.db                  import models
from django.contrib.auth.models import User
from django.core.cache          import cache
from django.db.models.signals   import pre_delete
from django.conf                import settings

from sorl.thumbnail.fields  import ImageWithThumbnailsField
from sorl.thumbnail.base    import ThumbnailException
import pytz

from core.util              import slugify, unique_field, get_current_campaign
from organization.models    import Organization

NO_DATA = 'NO_DATA'
GRADES = ['A+', 'A', 'B+', 'B', 'C+', 'C']


class Group(models.Model):
    """A Group of users.
    Could be a department (Finance), 
    a social grouping (Running club), 
    or a demographic group (age, gender).
    """

    name = models.CharField(max_length=150)
    organization = models.ForeignKey(Organization)
    avg_user = models.ForeignKey('Profile', null=True)

    def __unicode__(self):
        return self.name
GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'))


class ProfileManager(models.Manager):
    """Methods above the level of a single Profile"""

    def unique_username(self, first_name, last_name, splitter='-'):
        """A username for user with given name"""

        username = slugify(first_name + splitter + last_name, max_len=30)
        username = unique_field(username, User, 'username')
        return username

    def cache_key_auth_user(self, user_id):
        """Key under which to cache django auth.User object for this id"""
        return 'ge_auth_user_%d' % user_id

    def cache_key_geuser(self, auth_userid):
        """Key under which to cache Profile object for this auth user id"""
        return 'ge_geuser_%d' % auth_userid

    def get_cached_auth_user(self, user_id):
        """Get a django.contrib.auth.models.User, using the cache"""

        cache_key = self.cache_key_auth_user(user_id)
        user = cache.get(cache_key)
        if not user:
            user = User.objects.get(pk=user_id)
            cache.set(cache_key, user)
        return user

    def get_cached_by_auth_userid(self, auth_userid):
        """Get a Profile, using the cache"""

        cache_key = self.cache_key_geuser(auth_userid)
        geuser = cache.get(cache_key)
        if not geuser:
            geuser = Profile.objects.get(user__id=auth_userid)
            cache.set(cache_key, geuser)
        return geuser


class Profile(models.Model):
    "Good Energy User Profile. The extra fields that aren't in the Django user"
    
    objects = ProfileManager()

    user = models.ForeignKey(User, unique=True)
    avatar = ImageWithThumbnailsField(upload_to='user_pictures/', 
                                      thumbnail={'size': (50, 50)},
                                      null=True, blank=True)
    
    is_system_user = models.BooleanField(default=False)
    timezone = models.CharField(max_length=100, default='UTC')
    
    about = models.TextField(blank=True, null=True, 
                help_text='User editable section of profile')
    compared_to_average = models.FloatField(default=0,
                help_text='How does this user compare to the overall average?')
    participation_points = models.IntegerField(default=1)
    inspiration_points = models.IntegerField(default=1)
    inspiration_points_credit = models.IntegerField(default=1)

    organization = models.ForeignKey(Organization, null=True, blank=True,
        help_text='Organization a user can administer, and used for reporting')

    created = models.DateTimeField(auto_now_add=True)

    groups = models.ManyToManyField(Group, null=True, blank=True)

    employer = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=50, null=True, blank=True) 

    is_new_user = models.BooleanField(default=True)

    referer = models.ForeignKey('self', null=True, blank=True, 
            help_text='User who signed up this user')

    class Meta:                     # pylint: disable-msg=W0232,R0903
        "Django object config"
        verbose_name = 'user'
        ordering = ('user__username',)
        
    def __unicode__(self):
        user = self.get_user()
        full_name = user.get_full_name()
        if full_name:
            return full_name
        else:
            return user.username

    def get_user(self):
        """Like self.user except uses the cache if possible"""
        return Profile.objects.get_cached_auth_user(self.user_id)

    def delete(self, *args, **kwargs):  # pylint: disable-msg=W0221
        'Override Django method, to prevent deleting Actions we created'
        self.action_set.clear()
        super(Profile, self).delete(*args, **kwargs)

    def save(self, *args, **kwargs):    # pylint: disable-msg=W0221
        """Override django method to update the cache"""
        super(Profile, self).save(*args, **kwargs)
        cache.set(Profile.objects.cache_key_geuser(self.user_id), self)
        cache.set(Profile.objects.cache_key_auth_user(self.user_id), self.user)

    def get_absolute_url(self):
        """URL at which we view this users details - standard Django concept"""
        campaign = get_current_campaign()
        if not campaign:
            return 'ERROR'
 
        return '/' + campaign.slug + self.get_user().get_absolute_url()

    def rank(self, campaign):
        """School type grade for how well user is doing"""
        exact = self.ranking(campaign)
        total = campaign.users.count()

        num_rank = int((float(exact) / total) * len(GRADES))

        # Very last user gets 6, so move down to 5
        return GRADES[min(num_rank, 5)] 

    def ranking(self, campaign):
        """Order in total campaign participants of this user on 
        overall indicator"""

        num_above = campaign.users\
                .filter(compared_to_average__gt=self.compared_to_average)\
                .count()

        # If no-one is better than us, we rank as number 1, and so on down
        return num_above + 1  

    def add_participation_points(self, points=1):
        """Adds participation points to this users total. Saves the user"""
        self.participation_points += points 
        self.save()

    def give_inspiration_point(self, geuser):
        """Give someone an inspiration point from our credit"""

        self.inspiration_points_credit -= 1
        geuser.inspiration_points += 1
        self.save()
        geuser.save()

    def profile_pic_filename(self, abspath=False, ext=None, variant=None):
        """Path of the original profile picture they uploaded.
        
        @param ext File extension ('png', 'jpg', etc).
        If the file doesn't exist yet, you must provide the extension.
        
        @param abspath Return an absolute path? 
        If False, it returns a path suitable for setting on the ImageField.
        
        @param variant [dark|full]
        - full means return filename of the full size original 
            upload (pre-crop). 
        - dark means return filename of a darkened version of the picture, 
            useful as an overlay when cropping. If the darkened version 
            doesn't exist it is generated. 
        The full file must exist.
        """
        
        import os.path
        import glob
        import Image

        profile_meta = Profile._meta    # pylint: disable-msg=W0212
        avatar_dir = profile_meta\
                        .get_field_by_name('avatar')[0]\
                        .upload_to  
        
        root = os.path.join(settings.MEDIA_ROOT, avatar_dir) 

        # Get the extension
        if not ext:
            
            if self.avatar:
                ext = self.avatar.name[-3:]
            else:
                filename = 'full_' + str(self.id)
                try:
                    ext = glob.glob(
                            os.path.join(root, filename + '.*')
                            )[0][-3:]
                except IndexError:
                    raise IOError('No such file: ' + filename + '.*')

        # Build the filename
        if variant == 'dark':
            filename = 'full_' + str(self.id) + '.' + ext
            
            darken = Image.open(os.path.join(root, filename))
            darken = darken.point(lambda p: p * 0.6)
            
            filename = filename.replace('full_', 'dark_')
            darken.save(os.path.join(root, filename))
            
        elif variant == 'full':
            filename = 'full_' + str(self.id) + '.' + ext
            
        else:
            filename = str(self.id) + '.' + ext
            
        if abspath:
            return os.path.join(root, filename)
        else:
            return os.path.join(avatar_dir, filename)
     
    def recalc_points(self):
        'Recalculates this users participation points'
        from indicator.models import Answer
        from status.models import Entry, EntryComment
       
        answers = Answer.objects.filter(user=self).count()
        status_updates = Entry.objects.filter(who=self).count()
        comments = EntryComment.objects.filter(who=self).count() 
    
        self.participation_points = answers + status_updates + comments
        self.save()
    
    def update_compared_to_average(self, campaign, action_date):
        """Updates the compared_to_average field for given campaign and day"""
        from indicator.models import Indicator
        
        overall = Indicator.objects.overall_indicator(campaign)
        _, new_distance = overall.compared_to_average(self, action_date)

        if self.compared_to_average != new_distance:
            self.compared_to_average = new_distance
            self.save()
        
    def local_datetime(self):
        """The current datetime in this users timezone: 
            datetime.datetime.now() with correct tz"""
        return datetime.datetime.now(pytz.timezone(self.timezone))

    def local_to_utc(self, date_to_convert):
        """Convert dt from users timezone to utc"""
        user_tz = pytz.timezone(self.timezone)
        datetime_to_convert = datetime.datetime.combine(date_to_convert, 
                                                        datetime.time())
        datetime_tz = user_tz.localize(datetime_to_convert)
        return datetime_tz.astimezone(pytz.utc)

    def as_map(self):
        """Basic user information as a map."""

        result = {}
        
        result['id'] = self.id
        result['label'] = unicode(self)     # jQuery UI needs label attribute
        
        return result
 
    def has_pic(self):
        """Has this user uploaded a picture to their profile yet?"""
        return bool(self.avatar)

    def thumb_url(self):
        'URL of this users thumb, or of the default thumb'

        if self.has_pic():
            try:
                # Split between media servers based on odd or even user id
                media_server_url = (settings.MEDIA_URL_1 
                                if self.id % 2 == 0 else settings.MEDIA_URL_2)
                url = unicode(self.avatar.thumbnail)
                url = url.replace(settings.MEDIA_URL, media_server_url)
                return url
            except ThumbnailException:
                pass

        return settings.DEFAULT_PROFILE_PIC_URL

    def pic_url(self):
        """URL of the full size profile picture for this user, or default"""

        if self.has_pic():
            # Split between media servers based on odd or even user id
            media_server_url = (settings.MEDIA_URL_1 
                                if self.id % 2 == 0 else settings.MEDIA_URL_2)
            url = unicode(self.avatar.url)
            url = url.replace(settings.MEDIA_URL, media_server_url)
            return url
        else:
            return settings.DEFAULT_PROFILE_PIC_URL

    def as_json(self):
        'JSON representation of the basic attributes of this user'
        return JSONEncoder().encode(self.as_map())

    def get_profile(self):
        'Allows a Profile to be substituted for an auth.User in templates'
        return self


def _map_by_date(answer_list):
    'Converts an iterable of answers into a map of action_date:answer_num'
    result = {}
    for answer in answer_list:
        result[answer.action_date] = answer.answer_num
    return result    


def clear_actions(sender, **kwargs):    # pylint: disable-msg=W0613
    """Clears the set of Actions this user created, 
    so that they don't get cascade deleted"""
    profile = kwargs['instance']
    profile.action_set.clear()


pre_delete.connect(clear_actions, sender=Profile)

