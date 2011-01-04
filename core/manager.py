""" http://<domain>/manager/ interface - Customer admin interface.
Customised version of regular django admin.
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
# pylint: disable-msg=R0904

from django                 import forms   
from django.contrib         import admin
from django.contrib.auth    import logout
from django.http            import HttpResponseRedirect

from campaign.models import Campaign
from indicator.models import Indicator, IndicatorLikert, IndicatorNumber
from action.models import Action
from action.view_objects import ActionView
from status.models import Entry, EntryComment
from profile.models import Profile


class Manager(admin.AdminSite):
    'Our custom admin site'
    index_template = 'admin/index_manager.html'

    def index(self, request, extra_context=None):
        'View method to render the front page of manager site'

        if not extra_context:
            extra_context = {}

        try:
            geuser = request.user.get_profile()
        except Profile.DoesNotExist:
            logout(request)
            # Redirect to ourselves, which will force manager login 
            return HttpResponseRedirect( request.path )

        org = geuser.organization

        # Campaigns
        campaign_list = Campaign.objects.filter(organization = org)
        extra_context['campaign_list'] = campaign_list

        # Actions
        extra_context['action_list'] = Action.objects.\
                filter(campaign__in = campaign_list).\
                order_by('title')

        # Status updates
        extra_context['entry_list'] = Entry.objects.\
                    filter(campaign__in = campaign_list).\
                    order_by('-when')[:10]

        return super(Manager, self).index(request, extra_context=extra_context)

'''
class IndicatorFormSet(BaseInlineFormSet):
    'Customises which data the admin sees for inline indicators'

    def get_queryset(self):
        'Django QuerySet for inline indicators within a campaign'
        return super(IndicatorFormSet, self).get_queryset().filter(is_synthetic = False)
'''

class IndicatorAdmin(admin.ModelAdmin):
    'Admin for manager app'

    model = Indicator
    #formset = IndicatorFormSet
    exclude = ['is_synthetic', 'created']

    def queryset(self, request):
        'Django QuerySet limited by users organization'
        org = request.user.get_profile().organization
        return Indicator.objects.filter(
                is_synthetic = False,
                campaign__organization = org)

class IndicatorLikertAdmin(admin.ModelAdmin):
    """Custom admin for IndicatorLikert"""
    model = IndicatorLikert
    exclude = ['is_synthetic', 'created']

    def queryset(self, request):
        'Django QuerySet limited by users organization'
        org = request.user.get_profile().organization
        return IndicatorLikert.objects.filter(
                is_synthetic = False,
                campaign__organization = org)

    def save_model(self, request, indicator, form, change):
        """Force cache refresh"""
        super(IndicatorLikertAdmin, self).save_model(request, indicator, form, change)
        Indicator.objects.all_regular_indicators(indicator.campaign, force=True)

class IndicatorNumberAdmin(admin.ModelAdmin):
    """Custom admin for IndicatorNumber"""
    model = IndicatorNumber
    exclude = ['is_synthetic', 'created']

    def queryset(self, request):
        'Django QuerySet limited by users organization'
        org = request.user.get_profile().organization
        return IndicatorNumber.objects.filter(
                is_synthetic = False,
                campaign__organization = org)

    def save_model(self, request, indicator, form, change):
        """Force cache refresh"""
        super(IndicatorNumberAdmin, self).save_model(request, indicator, form, change)
        Indicator.objects.all_regular_indicators(indicator.campaign, force=True)

class CampaignAdmin(admin.ModelAdmin):
    'Custom admin for Campaign'

    list_display = ['name', 'start_date', 'end_date', 'num_users', 'view_on_site']
    exclude = ['organization', 'users']
    prepopulated_fields = {'slug': ('name',)}
    #filter_horizontal = ['users']

    def save_model(self, request, campaign, form, change):
        'Add in the organization prior to saving'
        campaign.organization = request.user.get_profile().organization
        super(CampaignAdmin, self).save_model(request, campaign, form, change)

        # Force cache refresh
        #Indicator.objects.all_regular_indicators(campaign, force=True)

    def queryset(self, request):
        'Django QuerySet of what to show in the admin - we narrow for this users org'
        return Campaign.objects.filter(organization = request.user.get_profile().organization)

class EntryCommentForm(forms.ModelForm):
    'Form for entry comments in admin site'

    comment = forms.CharField( 
            widget=forms.Textarea(attrs={'rows': 2, 'cols': 60}), 
            label='comment')

    class Meta:
        """Django config"""
        model = EntryComment

class EntryCommentAdmin(admin.TabularInline):
    'Inline admin for comments on status entries'

    model = EntryComment
    form = EntryCommentForm
    template = 'status/admin/entry_comment_inline.html'

    extra = 0
    ordering = ['-created']
    exclude = ['user']

class EntryForm(forms.ModelForm):
    'Form to display an Entry on the admin site'

    msg = forms.CharField(
            widget=forms.TextInput(attrs={'size': 125}),
            label='Message')

    class Meta:
        """Django config"""
        model = Entry

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.campaign = kwargs['instance'].campaign

class EntryAdmin(admin.ModelAdmin):
    'Django admin for status updates'

    list_display = ['who_link', 'msg', 'when', 'comments']
    list_display_links = ['msg']
    ordering = ['-when']

    date_hierarchy = 'when'
    search_fields = ['msg', 'who__user__username']
    filter_horizontal = ['liked_by']

    inlines = [EntryCommentAdmin, ]
    form = EntryForm
    exclude = ['campaign']

    change_form_template = 'status/admin/change_form.html'

    def who_link(self, obj):
        'Link tag to the user'
        geuser = obj.who
        return '<a href="/manager/profile/profile/%d/">%s</a>' % (geuser.id, geuser)
    who_link.short_description = 'User' # pylint: disable-msg=W0612
    who_link.allow_tags = True # pylint: disable-msg=W0612

    def comments(self, obj):
        'Number of comments on this entry'
        return obj.entrycomment_set.count()

    def queryset(self, request):
        'QuerySet of Entries to show in admin'
        org = request.user.get_profile().organization
        return Entry.objects.filter(campaign__in = org.campaign_set.all())

class ProfileForm(forms.ModelForm):
    'Form for editing a profile in the admin'

    model = Profile

class ProfileAdmin(admin.ModelAdmin):
    'Django admin for users'

    list_display = ['avatar_img', 
                    'name', 
                    'email',
                    'employer',
                    'city',
                    'points']
    search_fields = ['user__username']

    list_per_page = 25

    form = ProfileForm
    exclude = ['is_system_user', 'organization']

    def name(self, obj):
        """User full name as link to user profile"""
        return '<a href="/manager/profile/profile/%d/">%s</a>' % (obj.id, unicode(obj))
    name.allow_tags = True                      # pylint: disable-msg=W0612
    name.admin_order_field = 'user__username'   # pylint: disable-msg=W0612

    def email(self, obj):
        """auth.User email address"""
        return obj.user.email

    def points(self, obj):
        """Label participation_points as points"""
        return obj.participation_points

    def city(self, obj):
        """Label postal_code as city"""
        return obj.postal_code

    def avatar_img(self, obj):
        'img tag of this user'
        if obj.avatar and obj.avatar.thumbnail:
            thumb = obj.avatar.thumbnail.absolute_url
            html = u'<img src="%s" alt="Picture of %s" />' % (thumb, unicode(obj))
            return html 
        else:
            return 'No avatar'

    avatar_img.allow_tags = True                # pylint: disable-msg=W0612
    avatar_img.short_description = 'avatar'     # pylint: disable-msg=W0612

    def queryset(self, request):
        """Django QuerySet of profiles visible to this user"""
        org = request.user.get_profile().organization
        campaign_list = Campaign.objects.filter(organization = org)

        return Profile.objects.filter(is_system_user=False, campaign__in = campaign_list)

# Runs when imported from root urls.py'

class ActionAdmin(admin.ModelAdmin):
    """Django admin for actions"""

    list_display = ['title', 'description', 'pledge_count']
    exclude = ['comment_count']

    def queryset(self, request):
        """Django QuerySet for Actions visible to this user"""
        org = request.user.get_profile().organization
        campaign_list = Campaign.objects.filter(organization = org)

        return Action.objects.filter(campaign__in = campaign_list)

    def save_model(self, request, action, form, change):
        """Clear the cache"""
        super(ActionAdmin, self).save_model(request, action, form, change)
        Action.objects.clear_dashboard_cache(action.campaign)
        ActionView.clear_popular_cache(action.campaign)

SITE = Manager()
SITE.register(Profile, ProfileAdmin)
SITE.register(Campaign, CampaignAdmin)
SITE.register(Indicator, IndicatorAdmin)
SITE.register(IndicatorLikert, IndicatorLikertAdmin)
SITE.register(IndicatorNumber, IndicatorNumberAdmin)
SITE.register(Action, ActionAdmin)
SITE.register(Entry, EntryAdmin)

