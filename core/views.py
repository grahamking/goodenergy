"""Controllers / page logic for Good Energy"""

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
import logging
import random
from json import JSONEncoder

from django.shortcuts               import render_to_response
from django.template                import RequestContext
from django.template.loader         import render_to_string
from django.core.urlresolvers       import reverse
from django.core.cache              import cache
from django.http                    import HttpResponseRedirect
from django.core.mail               import mail_admins
#from django.db                     import connection

from indicator.models       import Indicator, Answer
from indicator.forms        import indicator_form
from status.models          import Entry
from status.view_objects    import EntryView
from profile.models         import Group, Profile
from action.models          import Action, Pledge
from action.view_objects    import ActionView

from core.forms import ContactForm
from core.util import get_current_organization, json_encoder_default
from core.util import chop_campaign, get_current_campaign
from core.util import ge_login_required

@ge_login_required
def dashboard(request, campaign_slug, indicator_id):
    "Home page"

    response_map = {}

    try:
        geuser = request.user.get_profile()
    except Profile.DoesNotExist:
        return reverse('registration_logout', kwargs={'campaign_slug': campaign_slug})

    campaign = get_current_campaign()
    campaign.add_user(geuser)

    if campaign.get_end_date(geuser) < datetime.date.today():
        url = reverse('results', kwargs={'campaign_slug': campaign.slug})
        return HttpResponseRedirect(url)

    indicator_list = Indicator.objects.all_regular_indicators(campaign) 
    response_map['indicator_list'] = indicator_list

    response_map['one_week_ago'] = datetime.datetime.now() - datetime.timedelta(7)
    
    indicator = None

    try:
        next_indicator = Indicator.objects.next(geuser, campaign)
        response_map['last_answered'] = next_indicator
    except Indicator.DoesNotExist:
        next_indicator = None
        response_map['is_done'] = True

    if indicator_id:
        try:
            indicator = Indicator.objects.get_cached(campaign, long(indicator_id))
        except Indicator.DoesNotExist:
            return HttpResponseRedirect('/')
    else:
        if next_indicator:
            indicator = next_indicator
        else :
            url = reverse('results', kwargs={'campaign_slug': campaign.slug})
            return HttpResponseRedirect(url)

    yesterday = geuser.local_datetime().date() - datetime.timedelta(1)
    try: 
        response_map['current_answer'] = \
            Answer.objects.get(
                user = geuser,
                indicator_id = indicator.id, 
                action_date = yesterday
            )
    except Answer.DoesNotExist:
        pass

    try:
        previous = Answer.objects.\
                filter(
                    user = geuser,
                    indicator_id = indicator.id,
                    action_date__lt = yesterday).\
                order_by('-action_date')[0]
    except (Answer.DoesNotExist, IndexError):
        previous = None

    response_map['next'] = indicator_form(indicator=indicator, user=geuser, previous=previous)

    if not indicator.image:
        # If no image we display a bar graph
        indicator_view = indicator.view(geuser, Indicator.objects.average_user())
        encoder = JSONEncoder(default = json_encoder_default)
        response_map['indicator_json'] = encoder.encode(indicator_view) 

    response_map['recent_activity_list'] = EntryView.recent_activity(campaign)

    popular_actions = ActionView.popular(campaign, geuser)
    response_map['popular_actions'] = popular_actions

    all_actions = list(popular_actions)
    random.shuffle(all_actions)
    response_map['all_actions'] = all_actions

    response_map['status_dashboard'] = _status_dashboard(request, response_map, campaign, geuser)
    response_map['action_dashboard'] = _action_dashboard(request, response_map, campaign, geuser)

    return render_to_response(
            'dashboard.html', 
            response_map, 
            context_instance=RequestContext(request))

def _status_dashboard(request, response_map, campaign, geuser):
    """HTML for the status part of the dashboard"""

    cache_key = Entry.objects.dashboard_cache_key(campaign, geuser)
    html = cache.get(cache_key)
    if not html:
        html = render_to_string(
                'status/status_dashboard_include.html', 
                response_map,
                context_instance=RequestContext(request))
        cache.set(cache_key, html) 

    return html

def _action_dashboard(request, response_map, campaign, geuser):
    """HTML for the action part of the dashboard"""

    cache_key = Action.objects.dashboard_cache_key(campaign, geuser)
    html = cache.get(cache_key)
    if not html:
        html = render_to_string(
                'action/action_dashboard_include.html', 
                response_map,
                context_instance=RequestContext(request))
        cache.set(cache_key, html) 

    return html

@ge_login_required
def results(request, campaign_slug, indicator_id = None):
    'Display the results'

    response_map = {'is_done': True}

    try:
        geuser = request.user.get_profile()
    except Profile.DoesNotExist:
        return reverse('registration_logout', kwargs={'campaign_slug': campaign_slug})

    organization = get_current_organization()

    campaign = get_current_campaign()

    overall_indicator = Indicator.objects.overall_indicator(campaign)
    response_map['overall_indicator'] = overall_indicator

    indicator_list = Indicator.objects.all_regular_indicators(campaign)
    response_map['indicator_list'] = indicator_list

    if not indicator_id and 'indicator_id' in request.REQUEST:
        indicator_id = request.REQUEST['indicator_id']

    if indicator_id:
        indicator = Indicator.objects.get(pk=indicator_id).subclass()
    else:
        indicator = overall_indicator
    response_map['current_indicator'] = indicator

    from_user = geuser
    if 'from' in request.GET and request.GET['from'] != 'me':
        from_group_id = request.GET['from']
        from_user = Group.objects.get(pk = from_group_id)
    response_map['from_user'] = from_user

    to_user = Indicator.objects.average_user()
    is_compare_to_all = True
    if 'to' in request.GET and request.GET['to'] != 'all':
        to_group_id = request.GET['to']
        to_user = Group.objects.get(pk = to_group_id)
        is_compare_to_all = False
    response_map['to_user'] = to_user
    response_map['is_compare_to_all'] = is_compare_to_all

    indicator_view = indicator.view(from_user, to_user)
    encoder = JSONEncoder(default = json_encoder_default)
    response_map['indicator_json'] = encoder.encode(indicator_view) 
    
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(1) 
    response_map['one_week_ago'] = now - datetime.timedelta(7)

    response_map['my_groups'] = geuser.groups.all()
    response_map['all_groups'] = Group.objects.filter(organization = organization)

    indicator_rating_list = []
    for ind in indicator_list:
        try:
            (ind.user_rating, ind.user_rating_exact) = ind.compared_to_average(geuser, yesterday)
            ind.user_rating_exact = abs(ind.user_rating_exact)
            indicator_rating_list.append(ind)
        except Answer.DoesNotExist:
            # User or Avg User has no answer for that day, don't display the indicator
            #ind.user_rating, ind.user_rating_exact = 0, 0
            pass

    indicator_rating_list.sort(key=lambda x: x.user_rating, reverse=True)
    response_map['indicator_rating_list'] = indicator_rating_list

    above, avg, below = [], [], []
    for indicator in indicator_rating_list:
        if indicator.user_rating > 0:
            above.append(indicator)
        elif indicator.user_rating == 0:
            avg.append(indicator)
        else:
            below.append(indicator)
    response_map['indicator_rating_above'] = above
    response_map['indicator_rating_avg'] = avg
    response_map['indicator_rating_below'] = below

    if campaign.get_end_date(geuser) < datetime.date.today() or 'completed' in request.GET:
        response_map['completed'] = is_completed = True

        my_stats = campaign.stats(geuser) 
        my_stats['completed_pledges'] = Pledge.objects.filter(
                is_completed=True, 
                user=geuser, 
                action__campaign = campaign)
        my_stats['pending_pledges'] = Pledge.objects.filter(
                is_completed=False, 
                user=geuser, 
                action__campaign = campaign)
        response_map['my_stats'] = my_stats

    else:
        response_map['completed'] = is_completed = False

    response_map['recent_activity_list'] = EntryView.recent_activity(campaign)

    popular_actions = ActionView.popular(campaign, geuser)
    response_map['popular_actions'] = popular_actions

    all_actions = list(popular_actions)
    if not is_completed:
        # Completed screen shows most popular actions first
        random.shuffle(all_actions)
    response_map['all_actions'] = all_actions

    response_map['status_dashboard'] = \
            _status_dashboard(request, response_map, campaign, geuser)
    response_map['action_dashboard'] = \
            _action_dashboard(request, response_map, campaign, geuser)

    return render_to_response(
            'results.html',
            response_map,
            context_instance=RequestContext(request))

@chop_campaign
def contact(request, title='Contact Us', success_url='/contact/thanks/'):
    'Contact Us form'
    
    form = ContactForm(request.POST or None)
    if request.method == 'POST':

        if form.is_valid():
            msg = u'Contact message from {name} ({email}): {message}'.format(
                                                        name = form.cleaned_data['name'],
                                                        email = form.cleaned_data['email'],
                                                        message = form.cleaned_data['message']
                                                        )
            logging.info(msg)   # Save it in case email is lost
        
            email_msg = (u'Contact message from {name} ({email}):\n'+
                         u'IP Address: {ip}\n'+
                         u'Browser: {browser}\n'+
                         u'\n'+
                         u'{message}\n')
        
            mail_admins('Message via Contact Form', 
                        email_msg.format(
                                        name = form.cleaned_data['name'],
                                        email = form.cleaned_data['email'],
                                        ip = request.META['REMOTE_ADDR'],
                                        browser = request.META['HTTP_USER_AGENT'],
                                        message = form.cleaned_data['message']         
                                        )
                        )

            return HttpResponseRedirect(success_url)

    return render_to_response('contact.html', 
                              {'form': form, 'title': title},
                              context_instance=RequestContext(request))

