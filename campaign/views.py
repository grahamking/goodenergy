"""Controller methods for campaign_manager module.
This is how customers administer their campaigns
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

import csv

from django.shortcuts               import render_to_response
from django.template                import RequestContext
from django.http                    import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers       import reverse
from django.core.exceptions         import PermissionDenied
from django.shortcuts               import get_object_or_404

from campaign.models        import Campaign
from campaign.forms         import CampaignForm
from profile.models         import Profile
from core.util              import get_current_organization, chop_campaign, ge_login_required

def redirect_to_default(request):
    """No campaign slug in URL. Redirect to the default campaign"""
    return HttpResponseRedirect(
            Campaign.objects.default(None, get_current_organization()).get_absolute_url()
            )

@ge_login_required
@chop_campaign
def campaign_list(request):
    'List the campaigns'

    response_map = {}

    geuser = request.user.get_profile()
    campaigns = Campaign.objects.filter(organization = geuser.organization)

    response_map['campaign_list'] = campaigns

    return render_to_response(
            'campaign/campaign_list.html',
            response_map,
            context_instance = RequestContext(request)
            )

@ge_login_required
@chop_campaign
def create_edit(request, campaign_id=None):
    'Create a new campaign or edit an existing one'

    geuser = request.user.get_profile()

    campaign = None
    if campaign_id:
        campaign = get_object_or_404(Campaign, pk=campaign_id)

    form = CampaignForm(geuser.organization, instance=campaign)
    if request.method == 'POST':
        form = CampaignForm(geuser.organization, request.POST, instance=campaign)

        if form.is_valid():
            form.save()
            if campaign:
                request.user.message_set.create(message='Campaign updated')
            else:
                request.user.message_set.create(message='New campaign created')
            return HttpResponseRedirect( reverse('campaign_list') )

    return render_to_response(
            'campaign/form.html', 
            {'form': form, 'campaign': campaign}, 
            context_instance = RequestContext(request))

@ge_login_required
@chop_campaign
def delete(request, campaign_id):
    'Delete a campaign'

    geuser = request.user.get_profile()
    campaign = get_object_or_404(Campaign, pk = campaign_id)
    if geuser.organization != campaign.organization:
        raise PermissionDenied('You do not have permission to delete that campaign')

    if request.method == 'POST':
        campaign.delete()
        request.user.message_set.create(message='Campaign %s deleted' % campaign)
        return HttpResponseRedirect( reverse('campaign_list') )

    return render_to_response(
            'campaign/delete_confirm.html',
            {'campaign': campaign},
            context_instance = RequestContext(request))

@ge_login_required
@chop_campaign
def users(request, campaign_id):
    """List of ACTIVE users in this campaign"""

    response_map = {}
    
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    response_map['campaign'] = campaign

    active_user_ids = list( campaign.active_user_ids() )
    user_map = Profile.objects.in_bulk(active_user_ids)
    user_result = user_map.values()
    user_result.sort(key = lambda u: u.user.username)
    response_map['users'] = user_result

    return render_to_response(
            'campaign/campaign_users.html',
            response_map,
            context_instance = RequestContext(request)
            )

@ge_login_required
def users_json(request, campaign_slug):
    """JSON list of users in this campaign. ALL users, not just active ones."""

    campaign = Campaign.objects.default(campaign_slug, get_current_organization())
    result = campaign.users_json()
    return HttpResponse(result, mimetype='application/json')

@ge_login_required
@chop_campaign
def campaigns_csv(request):
    'CSV of the campaigns for this users organization'

    current_user = request.user.get_profile()
    if not current_user.user.is_staff:
        raise PermissionDenied('Only administrators can view this file')

    org = current_user.organization
    campaigns = Campaign.objects.filter(organization = org)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=campaigns.csv'

    writer = csv.writer(response)
    writer.writerow([
        'Campaign Id',
        'Name',
        'Start Date',
        'End Date',
        'Is Default'
        ])

    for campaign in campaigns:
        writer.writerow([
            campaign.id,
            campaign.name,
            campaign.start_date,
            campaign.end_date,
            campaign.is_default
            ])

    return response

