"""Page logic for this app""" 

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
import csv

from django.shortcuts               import render_to_response, get_object_or_404
from django.template                import RequestContext
from django.core.urlresolvers       import reverse
from django.core.exceptions         import PermissionDenied
from django.http                    import HttpResponseRedirect, HttpResponse

from profile.models     import Profile
from indicator.models   import Indicator, Answer
from indicator.forms    import indicator_form, IndicatorCreateEditForm
from campaign.models    import Campaign
from core.util          import get_current_organization, chop_campaign, ge_login_required

class IndicatorView():
    'A display version of Indicator'
    
    def __init__(self, indicator):
        self.indicator = indicator
        self.answers = []
        self.group_avg = 0
        self.user_avg = 0
    
    def __getattr__(self, attr):
        'Wraps the indicator'
        return getattr(self.indicator, attr)


class AnswerView():
    'A display object which holds the data for one or two answers, which we can compare'
    def __init__(self, answer):
        
        self.action_date = answer.action_date
        self.num_value = answer.num_value
        self.value = answer.value
        
        self.compare_value = None
        self.compare_num_value = -1

@ge_login_required
@chop_campaign
def questions_json(request):
    'The indicators for display, with previous answers, in JSON format'

    current_user = request.user.get_profile()
    return HttpResponse(current_user.questions_json(), mimetype="application/json")

@ge_login_required
def answer_create_single(request, campaign_slug=None, indicator_id=None):
    """POST response to a single indicator
    
    @param indicator_id: Id of the Indicator who's question we are answering.
    If not given in the url, we look in GET and POST.
     
    @return: For AJAX call HttpResponse OK if success, ERROR plus some detail if failure.
    For an HTTP call, redirect to next indicator
    """
    
    if not indicator_id:
        try:
            indicator_id = request.REQUEST['indicator_id']
        except KeyError:
            return HttpResponse('ERROR - Missing indicator_id', mimetype='text/plain')
 
    indicator = Indicator.objects.get(pk = indicator_id).subclass()
    
    geuser = request.user.get_profile()
    
    if request.method == 'POST':
            
        form = indicator_form(request.POST, indicator=indicator, user=geuser)

        if not form.is_valid():
            return HttpResponse(
                    'ERROR - Invalid form - {err}'.format(err=unicode(form.errors)),
                    mimetype='text/plain')
        
        form.save()

        if request.is_ajax():
            return HttpResponse('OK')

    return redirect_to_indicator(request, campaign_slug=campaign_slug) 

def answer_table(request, user_id):
    "Displays a table of all the users answers"
    
    response_map = {}
    
    user = get_object_or_404(Profile, pk=user_id)
    response_map['user'] = user
    
    indicators = Indicator.objects.all().order_by('name')
    response_map['indicator_list'] = indicators
    
    first_date = None
    last_date = None
    answer_map = {} 
    for answer in Answer.objects.filter(user = user).order_by('created', 'indicator__name'):
        if not first_date:
            first_date = answer.action_date
        last_date = answer.action_date
        answer_map[ str(answer.action_date) +'_'+ str(answer.indicator.id) ] = answer
    
    answers = []
    current_date = first_date
    while current_date <= last_date:
        
        for indicator in indicators:
            try:
                current_answer = answer_map[str(current_date) +'_'+ str(indicator.id)]
            except KeyError:
                current_answer = {
                        'value': '', 
                        'action_date': current_date, 
                        'indicator': {'name': indicator.name}
                        }
                
            answers.append(current_answer)
            
        current_date += datetime.timedelta(1)
        
    response_map['answer_list'] = answers
    
    return render_to_response('indicator/answer_table.html',
                              response_map,
                              context_instance=RequestContext(request))

@ge_login_required
@chop_campaign
def create_edit(request, campaign_id=None, indicator_id=None):
    """Create a new indicator. 
    - Create must provide campaign_id,
    - Edit must provide indicator_id
    """

    indicator = None
    if indicator_id:
        indicator = get_object_or_404(Indicator, pk = indicator_id)
        campaign = indicator.campaign

    else:
        indicator = None
        campaign = get_object_or_404(Campaign, pk = campaign_id)

    form = IndicatorCreateEditForm(campaign, instance=indicator)
    if request.method == 'POST':
        form = IndicatorCreateEditForm(campaign, request.POST, instance=indicator)

        if form.is_valid():
            form.save()

            if indicator:
                request.user.message_set.create(message = 'Indicator updated')
            else:
                request.user.message_set.create(message = 'Indicator created')

            url = reverse('indicator_list', kwargs={'campaign_id': campaign.id})
            return HttpResponseRedirect( url )

    return render_to_response(
            'indicator/form.html',
            {'form': form, 'campaign': campaign, 'indicator': indicator},
            context_instance = RequestContext(request))

@ge_login_required
@chop_campaign
def indicator_list(request, campaign_id):
    'List of indicators for a specific campaign' 

    campaign = get_object_or_404(Campaign, pk = campaign_id)
    indicators = Indicator.objects.all_regular_indicators(campaign) 

    return render_to_response(
            'indicator/indicator_list.html',
            {'indicator_list': indicators, 'campaign': campaign},
            context_instance = RequestContext(request))

@ge_login_required
@chop_campaign
def delete(request, indicator_id):
    """Delete an indicator"""
    indicator = get_object_or_404(Indicator, pk = indicator_id)
    campaign = indicator.campaign

    geuser = request.user.get_profile()
    if geuser.organization != campaign.organization:
        raise PermissionDenied('You do not permissions to delete this indicator')

    if request.method == 'POST':

        indicator.delete()

        request.user.message_set.create(message = 'Indicator deleted')
        url = reverse('indicator_list', kwargs={'campaign_id': campaign.id})
        return HttpResponseRedirect( url )

    return render_to_response(
            'indicator/delete_confirm.html',
            {'indicator': indicator, 'campaign': campaign},
            context_instance = RequestContext(request))

@ge_login_required
def redirect_to_indicator(request, campaign_slug=None):
    'Redirects to the next indicator that needs an answer'

    try:
        geuser = request.user.get_profile()
    except Profile.DoesNotExist:
        # Admin user trying to access regular site
        return HttpResponseRedirect( 
                reverse('registration_logout', kwargs={'campaign_slug': campaign_slug}) )

    organization = get_current_organization()

    campaign = Campaign.objects.default(campaign_slug, organization)

    try:
        next_indicator = Indicator.objects.next(geuser, campaign)
        is_done = False
    except Indicator.DoesNotExist:
        is_done = True

    if is_done:
        url = reverse('results', kwargs={'campaign_slug': campaign.slug})
    else:
        url = reverse('indicator_home', 
                kwargs={'campaign_slug': campaign.slug, 'indicator_id': next_indicator.id})

    return HttpResponseRedirect(url)

@ge_login_required
@chop_campaign
def indicators_csv(request):
    'CSV of the indicators for this users campaigns'

    current_user = request.user.get_profile()
    if not current_user.user.is_staff:
        raise PermissionDenied('Only administrators can view this file')

    org = current_user.organization
    campaign_list = Campaign.objects.filter(organization = org)

    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=indicators.csv'

    writer = csv.writer(response)
    writer.writerow([
        'Campaign Id',
        'Campaign Name',
        'Indicator Id',
        'Indicator Type',
        'Position',
        'Name',
        'Question',
        'description',
        'created'
        ])

    for campaign in campaign_list:
        for indicator in campaign.indicator_set.all():
            writer.writerow([
                campaign.id,
                campaign.name,
                indicator.id,
                indicator.subclass().content_type,
                indicator.position,
                indicator.name,
                indicator.question,
                indicator.description,
                indicator.created
                ])

    return response

@ge_login_required
@chop_campaign
def answers_csv(request):
    'CSV of the answers for this users indicators'

    current_user = request.user.get_profile()
    if not current_user.user.is_staff:
        raise PermissionDenied('Only administrators can view this file')

    org = current_user.organization
    campaign_ids = Campaign.objects.filter(organization = org).values_list('id', flat=True)
    indicator_ids = Indicator.objects.\
            filter(campaign__id__in = campaign_ids).\
            values_list('id', flat=True)
    
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=answers.csv'

    writer = csv.writer(response)
    writer.writerow([
        'Answer Id',
        'Indicator Id',
        'User Id',
        'Action Date',
        'Numeric Value',
        'Text Value',
        'Is Skip',
        'Created'
        ])

    start_date = datetime.datetime.now() - datetime.timedelta(30)
    answer_list = Answer.objects.filter(
            indicator_id__in = indicator_ids, 
            action_date__gt = start_date).order_by('action_date')
    for answer in answer_list:

        writer.writerow([
            answer.id,
            answer.indicator_id,
            answer.user_id,
            answer.action_date,
            answer.answer_num,
            answer.answer_text,
            answer.is_skip,
            answer.created
            ])

    return response

