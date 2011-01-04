"""Controllers for the Action app
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

from django.shortcuts               import get_object_or_404
from django.http                    import HttpResponse, HttpResponseNotAllowed
from django.template                import RequestContext
from django.template.loader         import render_to_string

from core.util              import get_current_organization, get_current_campaign
from core.util              import chop_campaign, ge_login_required
from campaign.models        import Campaign
from profile.models         import Profile
from action.models          import Action, Pledge, Barrier
from action.view_objects    import ActionView
from indicator.views        import redirect_to_indicator

@ge_login_required
@chop_campaign
def pledge(request, action_id):
    """User pledges to perform an action"""

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    current_user = request.user.get_profile()
    action = get_object_or_404(Action, pk=action_id)

    action.pledge(current_user)
    ActionView.clear_popular_cache(action.campaign)    # TODO: Should be done by ge_worker

    action_view = ActionView(action, current_user)
    action_html = render_to_string(
            'action/action_full_include.html',
            {'action': action_view, 'geuser': current_user, 'expand': True},
            context_instance=RequestContext(request))
    return HttpResponse(action_html, mimetype='text/html') 

@ge_login_required
@chop_campaign
def done(request, action_id):
    """User completed an action"""

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    current_user = request.user.get_profile()
    action = get_object_or_404(Action, pk=action_id)

    user_pledge = Pledge.objects.get(action=action, user=current_user)
    user_pledge.is_completed = True
    user_pledge.save()

    action_view = ActionView(action, current_user)

    Action.objects.clear_dashboard_cache(action.campaign)
    ActionView.clear_popular_cache(action.campaign)    # TODO: Should be done by ge_worker

    action_html = render_to_string(
            'action/action_full_include.html',
            {'action': action_view, 'geuser': current_user, 'expand': True},
            context_instance=RequestContext(request))
    return HttpResponse(action_html, mimetype='text/html') 

@ge_login_required
@chop_campaign
def full(request, action_id):
    """HTML of an expanded action"""

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    current_user = request.user.get_profile()
    action = Action.objects.get(pk = action_id)
    action_view = ActionView(action, current_user)

    action_html = render_to_string(
            'action/action_full_include.html',
            {'action': action_view, 'geuser': current_user, 'expand': True},
            context_instance=RequestContext(request))
    return HttpResponse(action_html, mimetype='text/html') 

@ge_login_required
@chop_campaign
def barriers(request, action_id):
    """Updates the barriers that this user is facing"""

    action = get_object_or_404(Action, pk=action_id)
    current_user = request.user.get_profile()

    if request.method == 'POST':

        for barrier in current_user.barrier_set.filter(action=action):
            barrier.users.remove(current_user)

        for key in request.POST.keys():
            if not key.startswith('barrier-'):
                continue

            if key == 'barrier-new':
                title = request.POST['new_barrier_text']
                if title:
                    barrier = Barrier.objects.create(title=title, action=action)
                    barrier.save()
            else:
                try:
                    barrier_id = key.split('-')[1]
                    barrier = Barrier.objects.get(pk=int(barrier_id))
                except (ValueError, KeyError, IndexError):
                    pass

            if barrier:
                barrier.users.add(current_user)
            
        Action.objects.clear_dashboard_cache(action.campaign)

    html = render_to_string(
            'action/barrier_list.html', 
            {'action': ActionView(action, current_user), 'expand_barriers': True},
            context_instance=RequestContext(request))
    return HttpResponse(html, mimetype='text/html')

@ge_login_required
def user_actions(request, campaign_slug, username):
    """List of actions user has pledged to do or already done"""
    org = get_current_organization()
    user = get_object_or_404(Profile, user__username=username)
    campaign = get_object_or_404(Campaign, slug=campaign_slug, organization=org)

    query_set = Pledge.objects.\
            filter(action__campaign = campaign, user = user).\
            order_by('is_completed', '-created')
    actions = [ActionView(pledge_obj.action, user) for pledge_obj in query_set]

    html = render_to_string(
            'action/action_list_include.html',
            {'action_list': actions},
            context_instance=RequestContext(request))
    return HttpResponse(html, mimetype='text/html')

@ge_login_required
def search(request, campaign_slug):
    """Search actions"""

    campaign = Campaign.objects.default(campaign_slug, get_current_organization())

    query = request.REQUEST['q']
    query_set = Action.objects.filter(title__icontains = query, campaign=campaign)
    actions = [ActionView(action) for action in query_set]

    html = render_to_string(
            'action/action_list_include.html',
            {'action_list': actions},
            context_instance=RequestContext(request))
    return HttpResponse(html, mimetype='text/html')

@ge_login_required
def create(request, campaign_slug):
    """Create a new Action and Pledge on it"""

    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    geuser = request.user.get_profile()
    if not 'title' in request.POST or not 'description' in request.POST:
        return HttpResponse('ERROR: title and description are required',
                mimetype='text/plain')
    
    title = request.POST['title']
    description = request.POST['description']

    action = Action.objects.create(
            campaign = get_current_campaign(),
            title = title,
            description = description,
            created_by = geuser)

    action.pledge(geuser)
    ActionView.clear_popular_cache(action.campaign)

    return redirect_to_indicator(request, campaign_slug=campaign_slug) 

