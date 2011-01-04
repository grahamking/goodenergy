"""Controllers / Page logic for this app"""

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

import os.path
import csv
import random
import operator
from json import JSONEncoder

from django.shortcuts               import render_to_response
from django.template                import RequestContext
from django.template.loader         import render_to_string
from django.core.urlresolvers       import reverse
from django.contrib.auth.views      import logout
from django.contrib.auth.views      import password_reset as auth_password_reset
from django.contrib.auth.views      import password_reset_confirm as auth_password_reset_confirm
from django.contrib.auth.models     import User
from django.core.exceptions         import PermissionDenied
from django.core.cache              import cache
from django.conf                    import settings
from django.http                    import HttpResponseRedirect, HttpResponse
from django.http                    import HttpResponseNotAllowed

from profile.forms          import LoginForm, RegistrationForm, SettingsForm
from profile.models         import Profile
from profile.view_objects   import ProfileView
from core                   import gravatar
from core.models            import ShortURL
from core.util              import get_current_organization, json_encoder_default, chop_campaign
from core.util              import ge_login_required
from profile.forms          import PasswordResetForm
from profile.util           import save_picture
from campaign.models        import Campaign
from status.models          import Entry
from status.view_objects    import EntryView

'''
@ge_login_required
def search(request, campaign_slug):
    'Search users'
    
    response_map = {}
    
    if 'q' in request.GET:
        query = request.GET['q']
        response_map['query'] = query
        
        search_result = Profile.objects.exclude(is_system_user = True)
        
        by_username = search_result.filter(user__username__icontains = query)
        by_first = search_result.filter(user__first_name__icontains = query)
        by_last = search_result.filter(user__last_name__icontains = query)
        
        search_result = set( list(by_username) + list(by_first) + list(by_last) )
        
        if len(search_result) > 25:
            search_result = list(search_result)[:15]
        
    else:
        search_result = Profile.objects.exclude(is_system_user = True)[:10]
        
    response_map['user_list'] = search_result 

    return render_to_response('profile/home.html', 
                              response_map,
                              context_instance=RequestContext(request))
'''

def login(request, campaign_slug, form_class=LoginForm):
    'Log a user in'
    
    form = form_class(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.login(request)

            current_user = form.cached_user.get_profile()
            campaign = Campaign.objects.default(campaign_slug, get_current_organization())
            campaign.add_user(current_user)

            home_url = reverse('campaign_home', kwargs={'campaign_slug': campaign_slug})
            return HttpResponseRedirect(home_url) 
        
    return render_to_response('registration/login.html',
                              {'form': form},
                              context_instance=RequestContext(request))

def register(request, campaign_slug, form_class=RegistrationForm):
    'Join the site and log right on in'
    org = get_current_organization()

    if request.method == 'POST':
        form = form_class(request.POST, request.FILES, organization = org)

        if form.is_valid():
            current_user = form.save_and_login(request)

            campaign = Campaign.objects.default(campaign_slug, org)
            campaign.add_user(current_user)

            if form.has_picture():
                crop_url = reverse('profile_crop', kwargs={'campaign_slug': campaign_slug})
                return HttpResponseRedirect(crop_url +'?new=1')
            else:
                home = reverse('campaign_home', kwargs={'campaign_slug': campaign_slug})
                return HttpResponseRedirect(home) 
    else:
        form = form_class(organization = org)
    
    return render_to_response('registration/registration_form.html',
                              {'form': form},
                              context_instance=RequestContext(request))

def logout_then_login(request, campaign_slug):
    """Replaces django's logout_then_login, for our custom login url"""
    return logout(request, '/'+ campaign_slug + settings.LOGIN_URL)

def password_reset(request, campaign_slug):
    """Wrapper around django's password_reset"""
    redirect = reverse('password_reset_done', kwargs={'campaign_slug': campaign_slug})
    return auth_password_reset(
            request, 
            is_admin_site = True, 
            password_reset_form = PasswordResetForm, 
            post_reset_redirect = redirect)

def password_reset_confirm(request, campaign_slug, uidb36, token):
    """Wrapper around django's password_confirm"""
    redirect = reverse('password_reset_complete', kwargs={'campaign_slug': campaign_slug})
    return auth_password_reset_confirm(
            request,
            uidb36,
            token,
            post_reset_redirect=redirect)

def password_reset_complete(
        request, 
        campaign_slug, 
        template_name='registration/password_reset_complete.html'):
    """Copied from django, to add campaign_slug in the url. And tidied up."""
    response_map = {}
    response_map['login_url'] = '/%s%s' % (campaign_slug, settings.LOGIN_URL)
    return render_to_response(template_name, context_instance=RequestContext(request, response_map))

@ge_login_required
def profile_settings(request, campaign_slug):
    """Settings page. Ajax only"""

    current_user = request.user.get_profile()
    campaign = Campaign.objects.default(campaign_slug, get_current_organization())

    if request.method == 'POST':
        form = SettingsForm(current_user, get_current_organization(), request.POST) 
        if form.is_valid():
            form.save()

            if 'survey' in request.GET:
                # Survey doesn't change any visible fields, so no need to reload page,
                # and 'Upload profile pic' bubble only shows on first load, 
                # so redirect would clear it.
                return HttpResponse(
                        JSONEncoder().encode({'close': True}), 
                        mimetype='application/json')
            else:
                # Refresh the cache
                cache.delete( Entry.objects.dashboard_cache_key(campaign, current_user) )
                EntryView.refresh_recent_activity(campaign)
                campaign.users_json(force=True)

                campaign_url = reverse('campaign_home', kwargs={'campaign_slug': campaign_slug})
                return HttpResponse(
                        JSONEncoder().encode({'location': campaign_url}), 
                        mimetype='application/json')
    else:
        form = SettingsForm(current_user, get_current_organization())

    html = render_to_string(
            'profile/settings_include.html',
            {'form': form, 'campaign': campaign},
            context_instance=RequestContext(request))

    result = {'html': html, 'close': False}
    encoder = JSONEncoder(default = json_encoder_default)
    return HttpResponse(encoder.encode(result), mimetype='application/json')

@ge_login_required
def crop(request, campaign_slug):
    'Allow the user to select how to crop their profile picture, and then actually crop it'
    import Image
    
    base_width = 288
    base_height = 235
    
    response_map = {}
    geuser = request.user.get_profile()

    if 'picture' in request.FILES:
        # Check uploaded image is acutally an image
        if not request.FILES['picture'].content_type.startswith('image'):
            request.user.message_set.create(
                                message='Invalid file type - please select a jpg, png or gif file')
            
            return render_to_response('profile/avatar_crop.html',
                              response_map,
                              context_instance=RequestContext(request))
            
            
    has_pic = False
    if geuser.has_pic():
        current_pic = geuser.profile_pic_filename(abspath=True, variant='full')
        if os.path.exists(current_pic):
            has_pic = True
            response_map['has_pic'] = has_pic 
            image = Image.open( current_pic )
    
    if request.method == 'POST':

        if 'picture' in request.FILES:  # Uploaded new picture, save and go back to crop
            
            # Delete current picture
            try:
                current_full = geuser.profile_pic_filename(abspath=True, variant='full')
                os.unlink(current_full)
                current_dark = geuser.profile_pic_filename(abspath=True, variant='dark')
                os.unlink(current_dark)
            except (OSError, IOError):                                             # IGNORE:W0704
                # No previous picture - no problem
                pass
            
            # Save new pic
            new_profile_pic = request.FILES['picture']
            relative_pic_name = save_picture(geuser, new_profile_pic)
            geuser.avatar = relative_pic_name
            geuser.save()

            crop_url = reverse('profile_crop', kwargs={'campaign_slug': campaign_slug})
            return HttpResponseRedirect(crop_url)
        
        else:
            # Cropped picture, save and continue to home page
            left = int(request.POST['left'])
            top = int(request.POST['top'])
            width = int(request.POST['width'])
            height = int(request.POST['height'])
            
            cropped = image.crop( (left, top, width + left, height + top) )
            resized = cropped.resize( (base_width, base_height) )
            resized.save( geuser.profile_pic_filename(abspath=True) )
            
            geuser.avatar = geuser.profile_pic_filename(abspath=False)
            geuser.save()

            # Clear status dashboard from cache so new pic will show
            for campaign in geuser.campaign_set.all():
                cache.delete( Entry.objects.dashboard_cache_key(campaign, geuser) ) 

            home_url = reverse('campaign_home', kwargs={'campaign_slug': campaign_slug})
            return HttpResponseRedirect(home_url)
    
    if has_pic:
        (width, height) = image.size
        
        # The sizes we need to fill the picture box on the dashboard
        response_map['base_width'] = base_width
        response_map['base_height'] = base_height
        response_map['aspect_ratio'] = float(base_width) / float(base_height)
        
        response_map['crop_img_width'] = width
        response_map['crop_img_height'] = height
        
        response_map['start_width'] = min(width, base_width)
        response_map['start_height'] = min(
                height, 
                response_map['start_width'] / response_map['aspect_ratio'])
    
        response_map['crop_img'] = settings.MEDIA_URL + \
                                    geuser.profile_pic_filename(abspath=False, variant='full') +\
                                    '?no_cache='+ str(random.randint(0, 1000))
        
        response_map['crop_img_dark'] = \
                                    settings.MEDIA_URL + \
                                    geuser.profile_pic_filename(abspath=False, variant='dark') +\
                                    '?no_cache='+ str(random.randint(0, 1000))

    return render_to_response('profile/avatar_crop.html',
                              response_map,
                              context_instance=RequestContext(request))
 
'''
@ge_login_required
@chop_campaign
def detail(request, username):
    """JSON for a users profile. Has a 'name' and an 'html' attribute."""
    response_map = {}

    user = Profile.objects.get(user__username = username)
    response_map['user'] = ProfileView(user)

    is_me = user == request.user.get_profile()
    response_map['is_me'] = is_me

    response_map['stream'] = user.life_stream()

    html = render_to_string(
            'profile/detail_include.html',
            response_map,
            context_instance = RequestContext(request))

    json = JSONEncoder().encode({'html': html, 'name': unicode(user)})
    return HttpResponse(json, mimetype='application/json')
'''

@ge_login_required
def detail(request, campaign_slug, username):
    """Users profile."""
    response_map = {}

    campaign = Campaign.objects.default(campaign_slug, get_current_organization())
    response_map['campaign'] = campaign

    geuser = Profile.objects.get(user__username = username)
    response_map['user'] = ProfileView(geuser)

    is_me = geuser == request.user.get_profile()
    response_map['is_me'] = is_me

    achieve = []
    achieve.append( {'msg': 'Joined the campaign', 'when': geuser.created} )
    for pledge in geuser.pledge_set.filter(action__campaign = campaign).order_by('-created'):
        achieve.append( 
            {'type': 'Pledged', 'msg': pledge.action.title, 'when': pledge.created } 
        )
    achieve.sort( key=operator.itemgetter('when'), reverse=True )
    response_map['achieve'] = achieve
    
    star_count = int(geuser.participation_points / 10)
    response_map['star_count'] = range(star_count)

    entries = []
    for entry in geuser.entry_set.filter(campaign=campaign).order_by('-when'):
        entries.append( EntryView(entry) )
    response_map['activity_list'] = entries

    return render_to_response(
            'profile/detail.html',
            response_map,
            context_instance = RequestContext(request))

@ge_login_required
@chop_campaign
def give_inspiration_point(request, user_id):
    'Gives one of the current users inspiration point credits to user_id'

    user = Profile.objects.get(pk = user_id)
    current_user = request.user.get_profile()

    if current_user.inspiration_points_credit <= 0:
        return HttpResponse('ERROR: No points left to give', mimetype='text/plain')

    current_user.give_inspiration_point(user)

    return HttpResponse('OK', mimetype='text/plain')

@ge_login_required
@chop_campaign
def about(request):
    """GET: Returns the About Me field for this user. POST: Updates it.
    Only POST is used by the app"""
    
    geuser = request.user.get_profile()
    
    if request.method == 'GET':
        return HttpResponse(geuser.about, mimetype='text/plain')
    
    elif request.method == 'POST':
        new_about = request.POST['about']
        geuser.about = new_about
        geuser.save()
        return HttpResponseRedirect(geuser.get_absolute_url())
        
    else:
        return HttpResponseNotAllowed(['GET', 'POST'])

@ge_login_required
@chop_campaign
def users_csv(request):
    'Output a CSV file of all the users for this organizations campaigns'

    current_user = request.user.get_profile()
    if not current_user.user.is_staff:
        raise PermissionDenied('Only administrators can view this file')

    org = current_user.organization

    user_list = Profile.objects.\
            filter(organization = org, is_system_user = False).\
            select_related(depth=1)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=users.csv'

    writer = csv.writer(response)
    writer.writerow([
        'User Id',
        'Username', 
        'First name', 
        'Last name', 
        'Email', 
        'Avatar', 
        'Timezone', 
        'Compared To Average (%)', 
        'Participation Points', 
        'Inspiration Points', 
        'Created', 
        'Last Login', 
        'About'])

    for geuser in user_list:
        writer.writerow([
            geuser.id,
            geuser.user.username,
            geuser.user.first_name,
            geuser.user.last_name,
            geuser.user.email,
            geuser.avatar,
            geuser.timezone,
            geuser.compared_to_average,
            geuser.participation_points,
            geuser.inspiration_points,
            geuser.created,
            geuser.user.last_login,
            geuser.about
            ])

    return response

@chop_campaign
def is_email_registered(request):
    "Expects 'email' as a GET param, prints 1 if email in database, 0 if not"

    if not 'email' in request.GET:
        return HttpResponse('0', mimetype='text/plain')

    email = request.GET['email']
    try:
        User.objects.get(email = email)
        return HttpResponse('1', mimetype='text/plain')
    except User.DoesNotExist:
        pass

    return HttpResponse('0', mimetype='text/plain')

@chop_campaign
def gravatar_url(request):
    "Expects 'email' as a GET param, prints the url for their gravatar. Errors print ERROR"

    if not 'email' in request.GET:
        return HttpResponse('ERROR', mimetype='text/plain')

    email = request.GET['email']
    result = gravatar.for_email(email)
    return HttpResponse(result, mimetype='text/plain')

@ge_login_required
def invite(request, campaign_slug):
    """Encourage users to invite their friends to the campaign"""

    response_map = {}
    campaign = Campaign.objects.default(campaign_slug, get_current_organization())
    response_map['campaign'] = campaign

    short_url = ShortURL.objects.make(campaign.get_refer_url())
    response_map['text'] = campaign.invite_message.replace('[url]', short_url) 

    return render_to_response(
            'profile/invite_include.html',
            response_map,
            context_instance=RequestContext(request))

