"""Controllers / page logic for this app."""

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

import datetime
from json import JSONEncoder

from django.shortcuts               import get_object_or_404
from django.http                    import HttpResponse, HttpResponseNotAllowed
from django.http                    import HttpResponseRedirect
from django.core.exceptions         import PermissionDenied
from django.template                import RequestContext
from django.template.loader         import render_to_string

from campaign.models        import Campaign
from core.util              import get_current_organization, get_current_user, json_encoder_default
from core.util              import chop_campaign, ge_login_required
from status.models          import Entry, EntryComment
from status.forms           import CommentForm
from status.view_objects    import EntryView
from profile.models         import Profile

@ge_login_required
def create(request, campaign_slug=None):
    "Create a new status update. Ajax POST only. Returns the new status's html"
    if request.method != 'POST':
        return HttpResponseNotAllowed('POST')
    geuser = request.user.get_profile()
    campaign = Campaign.objects.default(campaign_slug, get_current_organization())

    entry = Entry(who = geuser,
                  msg = request.POST['status'],
                  campaign = campaign)
    entry.save()
    EntryView.refresh_recent_activity(campaign)
    Entry.objects.clear_dashboard_cache(campaign)

    activity_html = render_to_string(
            'status/detail_include.html', 
           {'activity': EntryView(entry), 'geuser': geuser},
            context_instance=RequestContext(request))

    return HttpResponse(activity_html, mimetype='text/html')

@ge_login_required
@chop_campaign
def comment(request, object_id):
    """Comment on an activity. POST only. Ajax only"""
    geuser = request.user.get_profile()
    entry = get_object_or_404(Entry, pk=object_id)

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    form = CommentForm(request.POST, user=geuser, entry=entry) 
    if form.is_valid():
        new_comment = form.save()
        Entry.objects.clear_dashboard_cache(entry.campaign)
        EntryView.refresh_recent_activity(entry.campaign)

        one_week_ago = datetime.datetime.now() - datetime.timedelta(7)
        comment_html = render_to_string(
                'status/comment_include.html',
                {'comment': new_comment, 'one_week_ago': one_week_ago, 'geuser': geuser},
                context_instance=RequestContext(request))
        return HttpResponse(comment_html, mimetype='text/html') 

    return HttpResponse('ERROR: '+ form.errors, mimetype='text/plain') 

@ge_login_required
@chop_campaign
def comment_delete(request, object_id):
    """Delete a comment"""

    if not request.method == 'POST':
        return HttpResponseNotAllowed(['POST'])

    geuser = request.user.get_profile()
    comment_to_delete = get_object_or_404(EntryComment, pk=object_id)
    if comment_to_delete.user != geuser:
        raise PermissionDenied('Only the author of this comment can delete it')

    entry = comment_to_delete.entry
    comment_to_delete.delete()
    entry.update_comment_count()
    EntryView.refresh_recent_activity(entry.campaign)

    return HttpResponse('OK', mimetype='text/plain')

@ge_login_required
@chop_campaign
def activity_like(request, object_id):
    """Current user likes a status update. POST only, Ajax only"""

    geuser = request.user.get_profile()
    entry = get_object_or_404(Entry, pk=object_id)

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    entry.liked_by.add(geuser)
    
    Entry.objects.clear_dashboard_cache(entry.campaign)
    EntryView.refresh_recent_activity(entry.campaign)
    return HttpResponse('OK')

@ge_login_required
@chop_campaign
def activity_unlike(request, object_id):
    """Current user no longer likes an activity from the community feed.
    POST only, Ajax only."""
    
    geuser = request.user.get_profile()
    entry = get_object_or_404(Entry, pk=object_id)
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    entry.liked_by.remove(geuser)
    
    Entry.objects.clear_dashboard_cache(entry.campaign)
    return HttpResponse('OK')
        
@ge_login_required
def next_activity(request, campaign_slug):
    """Next most recent activity for everyone"""

    campaign = Campaign.objects.default(campaign_slug, get_current_organization())

    start = int( request.GET.get('start', 0) )

    recent_activity = [EntryView(entry) \
            for entry in Entry.objects.recent_activity(campaign, start=start)]
    html = ''
    if recent_activity:
        html = render_to_string(
                'status/list_include.html', 
                {'activity_list': recent_activity},
                context_instance=RequestContext(request))

    is_done = False
    if start + 5 >= Entry.objects.filter(campaign=campaign).count():
        is_done = True

    encoder = JSONEncoder(default = json_encoder_default)
    json = encoder.encode({'is_done': is_done, 'html': html})
    return HttpResponse(json, mimetype='application/json')
 
@ge_login_required
def user_activity(request, campaign_slug):
    """Most recent activity for given user as HTML snippet """
    
    campaign = Campaign.objects.default(campaign_slug, get_current_organization())
    if 'user_id' in request.GET:
        geuser = get_object_or_404(Profile, id = request.GET['user_id'])
    else:
        geuser = get_current_user()
    
    activity_qs = Entry.objects.filter(campaign=campaign, who=geuser)
    activity_list = [EntryView(entry) for entry in activity_qs]
    
    html = render_to_string(
            'status/list_include.html',
            {'activity_list': activity_list, 'geuser': geuser},
            context_instance=RequestContext(request))

    return HttpResponse(html, mimetype='text/html')

@ge_login_required
def clear_cache(request, campaign_slug):
    """Clear cached Entry objects. Called from manager admin"""
    org = get_current_organization()
    campaign = Campaign.objects.default(campaign_slug, org)
    Entry.objects.clear_dashboard_cache(campaign)
    EntryView.refresh_recent_activity(campaign)
    return HttpResponseRedirect('/manager/')

