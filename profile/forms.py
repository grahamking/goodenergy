""" Django forms for user registration and profile activity
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
# pylint: disable-msg=E1101,E1103

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import PasswordResetForm as AuthPasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.template import Context, loader
from django.utils.translation import ugettext_lazy as _
from django.utils.http import int_to_base36

import pytz

from profile.models import Profile, Group
from profile.util import save_picture
from core.util import get_current_campaign

class LoginForm(forms.Form):
    'Login form'
    
    email = forms.EmailField()
    password = forms.CharField(max_length=50, min_length=3, widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.cached_user = None

    def clean_email(self):
        'Check a user exists for this email address'
        try:
            user = User.objects.get(email = self.cleaned_data['email'])
            self.cached_user = user
        except User.DoesNotExist:
            raise forms.ValidationError('Email address not recognized')

        return self.cleaned_data['email']        

    def clean(self):
        'Check the password is correct'
        
        if not self.cached_user or not 'password' in self.cleaned_data:
            # Previous error, we don't need to run
            return
        
        auth_user = authenticate(username = self.cached_user.username, 
                                 password = self.cleaned_data['password'])
        if not auth_user:
            raise forms.ValidationError('Invalid password (Check Caps-Lock?)')

        self.cached_user = auth_user # Now cached_user is the authenticated user

    def login(self, request):
        'Actually login the user'
        login(request, self.cached_user)        


class RegistrationForm(forms.Form):
    """Data user needs to provide to join"""
    
    first_name = forms.CharField(max_length=100)
    last_name = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(max_length=50, min_length=4, widget=forms.PasswordInput())
    group = forms.ChoiceField(choices=[], required=False)
    picture = forms.ImageField(required=False)
    timezone = forms.ChoiceField(choices= [(tz, tz) for tz in pytz.common_timezones], 
                                 initial='America/Vancouver')
    
    def __init__(self, *args, **kwargs):
        org = kwargs.pop('organization')
        super(RegistrationForm, self).__init__(*args, **kwargs)

        group_choices = []
        group_choices.append( ('', '-----') )
        self.has_groups = False
        for group in Group.objects.filter(organization = org):
            group_choices.append( (group.id, group.name) )
            self.has_groups = True
        self.fields['group'].choices = group_choices

    def clean_email(self):
        "Validate that the supplied email address is unique for the site"
        
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact = email):
            raise forms.ValidationError(u'Email address already in use.')
        
        return email

    def save_and_login(self, request):
        'Create this user in the database, log that user in, and return the Profile'
        
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']

        #username = defaultfilters.slugify(self.cleaned_data['email'])[:30]
        username = Profile.objects.unique_username(first_name, last_name)
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        new_user = User.objects.create_user(username, email, password)
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.save()

        geuser = Profile(user = new_user, timezone=self.cleaned_data['timezone'])

        referer = None
        referer_id = None
        if 'f' in request.GET:
            referer_id = request.GET['f']
        elif 'f' in request.COOKIES:
            referer_id = request.COOKIES['f']
        if referer_id:
            try:
                referer = Profile.objects.get(pk = long(referer_id))
                referer.add_participation_points(points=5)
                referer.save()

                geuser.referer = referer
            except (Profile.DoesNotExist, ValueError):
                pass
        geuser.save()

        if self.cleaned_data['picture']:
            relative_pic_name = save_picture(geuser, self.cleaned_data['picture'])
            geuser.avatar = relative_pic_name
        #else:
        #    relative_pic_name = save_gravatar(geuser)

        geuser.save()
        
        if self.cleaned_data['group']:
            group_id = self.cleaned_data['group']
            group = Group.objects.get(pk = group_id)
            geuser.groups.add(group)

        user = authenticate(username=new_user.username, password=password)
        login(request, user)

        return geuser

    def has_picture(self):
        'Does this form have a picture uploaded to it'
        return self.cleaned_data['picture']

class PasswordResetForm(AuthPasswordResetForm):
    """Extends django's PasswordResetForm to include the campaign in the email template context"""

    def save(self, domain_override=None, email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator):
        """
        Generates a one-use only link for resetting password and sends to the user
        """
        from django.core.mail import send_mail
        for user in self.users_cache:
            if not domain_override:
                current_site = Site.objects.get_current()
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            t = loader.get_template(email_template_name)
            c = {
                # This line is the only difference to the django form
                'campaign': get_current_campaign(),

                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': int_to_base36(user.id),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': use_https and 'https' or 'http',
            }
            send_mail(_("Password reset on %s") % site_name,
                t.render(Context(c)), None, [user.email])


GENDER_CHOICES = (('U', '---'), ('M', 'Male'), ('F', 'Female'))
class SettingsForm(forms.Form):
    'User configuration'
    
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    email = forms.EmailField(label='Email address')
    timezone = forms.ChoiceField(choices= [(tz, tz) for tz in pytz.common_timezones])
    groups = forms.ModelMultipleChoiceField(queryset = None, required=False)

    #gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    #birthday = forms.DateField(required=False)
    #job_title = forms.CharField(max_length=100, required=False)
    employer = forms.CharField(max_length=100, required=False)
    postal_code = forms.CharField(max_length=50, required=False, label='City') 

    def __init__(self, geuser, organization, *args, **kwargs):
        self.geuser = geuser
        super(SettingsForm, self).__init__(*args, **kwargs)

        self.fields['first_name'].initial = self.geuser.user.first_name
        self.fields['last_name'].initial = self.geuser.user.last_name
        self.fields['email'].initial = self.geuser.user.email
        self.fields['timezone'].initial = self.geuser.timezone

        groups_queryset = Group.objects.filter(organization = organization)
        self.fields['groups'].queryset = groups_queryset 
        self.has_groups = bool( groups_queryset.count() )
        if self.has_groups:
            self.fields['groups'].initial = [group.id for group in self.geuser.groups.all()]

        #self.fields['gender'].initial = self.geuser.gender
        #self.fields['birthday'].initial = self.geuser.birthday
        #self.fields['job_title'].initial = self.geuser.job_title
        self.fields['employer'].initial = self.geuser.employer
        self.fields['postal_code'].initial = self.geuser.postal_code

    def save(self):
        'Write settings to the database'
        
        self.geuser.is_new_user = False

        user = self.geuser.user
        new_first = self.cleaned_data['first_name']
        new_last = self.cleaned_data['last_name']
        if new_first != user.first_name or new_last != user.last_name:
            user.first_name = new_first
            user.last_name = new_last
            user.username = Profile.objects.unique_username(new_first, new_last)

        user.email = self.cleaned_data['email']
        user.save()

        self.geuser.groups = self.cleaned_data['groups']
        self.geuser.timezone = self.cleaned_data['timezone']

        #self.geuser.gender = self.cleaned_data['gender']
        #self.geuser.birthday = self.cleaned_data['birthday']
        #self.geuser.job_title = self.cleaned_data['job_title']
        self.geuser.employer = self.cleaned_data['employer']
        self.geuser.postal_code = self.cleaned_data['postal_code']

        self.geuser.save()
        return self.geuser

