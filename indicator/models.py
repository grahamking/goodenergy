"""Models objects for the indicator app."""

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
#
# Django manages have many public methods
# pylint: disable-msg=R0904

import math
import datetime
import random
from collections import deque

from django.db import models
from django.db import connection
from django.db.models import Avg
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.db.models.fields.related import OneToOneField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

from profile.models import Profile, Group
from campaign.models import Campaign 
from core.util import get_current_user
from core import messaging
from indicator.util import answer_map_by_date

OVERALL_INDICATOR_NAME = 'OVERALL'
AVERAGE_USERNAME = 'AVERAGE'

def org_files_dir(instance, filename):
    'The path to store files for an instance of Indicator, relative to MEDIA_ROOT'
    return 'organization/'+ instance.campaign.organization.slug +'/'+ filename

class IndicatorManager(models.Manager):
    'Methods above the level of a single Indicator'
    
    def all_regular_indicators(self, campaign, force=False):
        'All the non-synthetic indicators, ordered by position, for this campaign'
        
        cache_key = 'ge_indicators_%d' % campaign.id
        result = cache.get(cache_key) or []

        if not result or force: 
            result = []
            app = models.get_app('indicator')
            for model in models.get_models(app):
                if Indicator in model.__bases__:

                    queryset = model.objects.filter(campaign = campaign, is_synthetic = False)
                    result.extend( list(queryset) )
            
            result.sort(key = lambda x: x.position)

            cache.set(cache_key, result)

        return result
    
    def get_cached(self, campaign, indicator_id):
        """Like regular get for pk = indicator_id, but from cache if possible"""
        all_inds = self.all_regular_indicators(campaign)
        for ind in all_inds:
            if ind.id == indicator_id:
                return ind
        raise Indicator.DoesNotExist()

    def next(self, user, campaign):
        """The next Indicator to ask this user, in the given campaign.
        @raise Indicator.DoesNotExist if this user has answered all their questions
        """
        ind_ids_by_pos = [ind.id for ind in self.all_regular_indicators(campaign)]

        day = user.local_datetime().date() - datetime.timedelta(1)
        todays_answers = Answer.objects.filter(
                indicator_id__in = ind_ids_by_pos,
                user = user, 
                action_date = day)

        # Remove the answered ones from the list
        for answer in todays_answers:
            ind_ids_by_pos.remove(answer.indicator_id)

        if not ind_ids_by_pos:
            raise Indicator.DoesNotExist('All indicators answered already')
        
        return self.get_cached(campaign, ind_ids_by_pos[0])

    def average_user(self):
        """The user (profile.Profile) who owns the average results. 
        This user answers the indicators each day with the average of everyone else answers
        """
        cache_key = 'ge_avg_user'   # Average user is common across all orgs and campaigns
        user = cache.get(cache_key)
        if not user:
            user = Profile.objects.get(user__username = AVERAGE_USERNAME)
            cache.set(cache_key, user)
        return user
    
    def overall_indicator(self, campaign):
        """The synthetic indicator that shows the campaign average over all a users 
        indicators for a given day"""
        cache_key = 'ge_overall_%d' % campaign.id
        ind = cache.get(cache_key)
        if not ind:
            ind = IndicatorNumber.objects.get(name = OVERALL_INDICATOR_NAME, campaign = campaign)
            cache.set(cache_key, ind)
        return ind

    def calculate_day_average(self, campaign, user, action_date):
        """Calculates and saves the average Answer for that user and action_date.
        Stored as an Answer against the overall_indicator"""
        
        overall_indicator = self.overall_indicator(campaign)
        
        overall_avg = 0
        count = 0

        # Load all this users answers, only including indicators for current campaign
        campaign_indicator_ids = [ind.id for ind in self.all_regular_indicators(campaign)] 
        answers = Answer.objects.filter(
                user = user, 
                action_date = action_date, 
                indicator_id__in = campaign_indicator_ids,
                is_skip=False).select_related(depth=1)

        for answer in answers:
            
            indicator = answer.indicator.subclass()
            if indicator.can_average():
                pct = indicator.as_percentage( answer.answer_num )
                overall_avg += pct
                count += 1

        try:
            result = overall_avg / count
        except ZeroDivisionError:
            result = 0
        
        if result != 0:
            (result_obj, _) = Answer.objects.get_or_create(
                                           user = user,
                                           indicator_content_type = overall_indicator.content_type,
                                           indicator_id = overall_indicator.id,
                                           action_date = action_date)
            result_obj.answer_num = result
            result_obj.save()

    '''
    def norm(self):
        'The aggregate average for the ALL user - the average of averages'
        return self.overall_indicator().moving_average( self.average_user() )
    '''

    '''
    def answer_list(self, geuser, campaign):
        'Data array of the users answers in campaign. Useful for graphing'

        answer_list = []
        
        average_user = self.average_user()
        for indicator in self.all_regular_indicators(campaign):
         
            indicator_view = indicator.view(geuser, average_user) 
            answer_list.append( indicator_view )
        
        return answer_list
    '''
    
    def create_overall_indicator(self, campaign):
        """Creates the OVERALL indicator for the given Campaign.
        If it already exists, does nothing.
        @return The overall indicator for this campaign.
        """

        overall_ind, _ = IndicatorNumber.objects.get_or_create(
                                campaign = campaign,
                                name = OVERALL_INDICATOR_NAME,
                                question = OVERALL_INDICATOR_NAME,
                                number_range_start = 1,
                                number_range_end = 100,
                                is_synthetic = True
                                )
        return overall_ind

class Indicator(models.Model):
    """An indicator, in the form of a question and possible answers"""
    
    objects = IndicatorManager()
    
    campaign = models.ForeignKey(Campaign)
    
    # Synthetic indicators don't have position
    position = models.IntegerField(null=True, blank=True, 
                                   help_text='Order to ask this question within the campaign') 
    
    name = models.CharField(max_length=50)
    question = models.TextField()
    
    is_synthetic = models.BooleanField(default=False)
    
    description = models.TextField()
    
    created = models.DateTimeField(default=datetime.datetime.now())

    image = models.ImageField(null=True, blank=True, upload_to=org_files_dir,
            help_text='Must be 300px wide by 226px high')
    
    class Meta:                                     # Doesn't need an __init__ IGNORE:W0232
        'Django config'
        ordering = ['position']
    
    def __unicode__(self):
        return self.name

    def get_manager_url(self):
        """URL of this indicator in the admin manager"""
        raise NotImplementedError()

    def as_map(self, user=None):
        'A map of all the data the client needs from this indicator'

        result = self.__dict__
        result['display_type'] = self.display_type()
        if user:
            previous_answer = self.previously(user)
            if previous_answer:
                result['previously'] = previous_answer.value

        return result
    
    def num_answers(self):
        """Number of answers to this indicator. Used by manager admin"""
        return Answer.objects.filter(indicator_id = self.id).count()

    def random_value(self):
        'A random value that makes sense for this indicator subclass'
        raise NotImplementedError()

    def can_graph(self):
        'Can this indicator be represented on a graph?'
        raise NotImplementedError()
    
    def can_average(self):
        'Can an average be calculated for this indicator?'
        raise NotImplementedError()

    def as_percentage(self, num):
        """Takes the numerical value from an Answer, and returns it as a percentage
        of the target value for this indicator.
        @raise ValueError if this indicator cannot be expressed as a percentage"""
        raise NotImplementedError()

    def answer_value(self, answer):
        "The value of this answer for display"
        raise NotImplementedError()

    def display_type(self):
        'The type of this indicator, to select which HTML block to show'
        raise NotImplementedError()

    def compared_to_average(self, user, action_date, tolerance=5):
        """Whether user is above, on, or below the average for this indicator on a given day
        @param tolerance Percentage around the average that is considered average. 
        Pass 0 to not use tolerance
        @return tuple of (toleranced_value, value). Negative numbers if user is below average, 
        0 if within 'tolerance'% of average, positive number if above average.
        """
        #user_moving_avg = self.moving_average(user=user, days_back=days_back)
        user_ans = Answer.objects.get(
                user=user, 
                action_date=action_date, 
                is_skip=False, 
                indicator_id=self.id)
        user_val = self.as_percentage(user_ans.answer_num)

        #avg_moving_avg = self.moving_average(days_back=days_back)
        avg_user = Indicator.objects.average_user()
        avg_ans = Answer.objects.get(user=avg_user, action_date=action_date, indicator_id=self.id)
        norm = self.as_percentage(avg_ans.answer_num)

        diff = user_val - norm
        toleranced = diff
        if -tolerance <= diff <= tolerance:
            toleranced = 0

        return (toleranced, diff)

    def average(self, average_date, group=None):
        """Calculates the average for this indicator on the given day across all users.
        Saves to the database.
        Stores the result as an Answer for average_user.
        @param group Calculate average for users of that group.
        """
        if group:
            average_user = group.avg_user
        else:
            average_user = Indicator.objects.average_user()
        
        average = 0
        count = 0
        
        answers = Answer.objects\
                .filter(indicator_id = self.id, 
                    action_date = average_date,
                    is_skip=False)\
                .exclude(user__is_system_user = True)\
                .select_related(depth=1)
        if group:
            answers = [ans for ans in answers if group in ans.user.groups.all()]

        for answer in answers:
            if answer.user.is_system_user:  # Don't include 'Average', 'admin', etc  
                continue
            
            if answer.answer_num:
                average += answer.answer_num
                count += 1
        
        if count != 0:
        
            (average_obj, _) = Answer.objects.get_or_create(
                                                     indicator_content_type=self.content_type,
                                                     indicator_id = self.id,
                                                     user = average_user,
                                                     action_date = average_date)
            
            average_obj.answer_num = float(average) / float(count)
            average_obj.save()

    def moving_average(self, user=None, days_back=None):
        """Average of everyones answers to this indicator over days_back.

        Pass a user to narrow for just that user.

        For the norm for an indicator just do: indicator.moving_average(),
        and for the users average, do indicator.moving_average(user=current_user)

        Pass the result to as_percentage if you want a percentage.

        If no user is given (the usual case) it averages the average_user's answers,
        so the average_users's values must be update to date.

        @param user An optional user to narrow the answer for
        @param days_back How many days to calculate the average over: 7 for last week, 30 for
        last month, etc. Defaults to all time.
        
        @return float The average
        """
        
        if not self.can_average():
            raise ValueError( self.__class__.__name__ +" can't be averaged")
        
        if not user:
            user = Indicator.objects.average_user()

        avg_qs = Answer.objects.filter(
                indicator_id = self.id, 
                user = user)

        if days_back:
            yesterday = user.local_datetime().date() - datetime.timedelta(1)
            start_date = yesterday - datetime.timedelta(days_back)

            avg_qs = avg_qs.filter(action_date__range = (start_date, yesterday))
            
        avg_obj = avg_qs.aggregate(Avg('answer_num'))
        
        avg = avg_obj['answer_num__avg'] or 0
        return avg
    
    def previously(self, user=None):
        """The users' most recent answer on this indicator
        @param user The user who's data we want - defaults to the current user
        @return An Answer object, or None if there is no previous.
        """
        
        if not user:
            user = get_current_user()
        
        try:
            prev = Answer.objects.filter(user = user, 
                                         indicator_id = self.id, 
                                         indicator_content_type = self.content_type,).\
                                  order_by('-action_date')[0]
            return prev
        except IndexError:
            return None

    @property
    def content_type(self):
        'The ContentType for this class'
        return ContentType.objects.get_for_model(self)

    def subclass(self):
        'The more specific type of indicator'
         
        if hasattr(self, 'indicator_ptr'):  # Already the subclass
            return self 
         
        for rel_obj in self._meta.get_all_related_objects():
            # In Django subclasses are linked to their parent via a OneToOneField
            if not isinstance(rel_obj.field, OneToOneField):
                continue
            
            try:
                subclass = getattr(self, rel_obj.var_name)
                return subclass
            except ObjectDoesNotExist:
                continue

        raise ObjectDoesNotExist('No subclass for indicator %d' % self.id)

    def participation(self):
        """How many people answered this question by day.
        @return Array of tuples (date, num_answers)
        """
        
        sql = "select action_date, count(*) from indicator_answer "+\
                "where indicator_id = %s group by action_date;"
                
        cursor = connection.cursor()
        cursor.execute(sql, [self.id])
        
        result = cursor.fetchall()
        return result

    def graph_ticks(self):
        'Javascript array of the Y values for the graph of this indicator'
        return [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

    def graph_labels(self):
        'Javascript array of the text labels for the graph of this indicator'
        return ['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%']

    def graph_has_numeric_legend(self):
        'Should we display the numeric value of the averages in the legend?'
        return True

    def view(self, from_user, to_user):
        """Map to represent this indicator in the gui. Includes answers.
        @param from_user The user or group to compare from. Usually the current
        logged in user or a group they belong to.
        @param to_user The user or group to compare to. Either a group, or
        the average user.
        """

        if not to_user:
            to_user = Indicator.objects.to_user()

        indicator_view = {}
        indicator_view['indicator_id'] = self.id
        
        from_data, to_data, from_avgs, to_avgs = self.answers_with_average(from_user, to_user)

        indicator_view['from_data'] = from_data
        indicator_view['to_data'] = to_data
        indicator_view['from_avg_data'] = from_avgs
        indicator_view['to_avg_data'] = to_avgs
        
        try:
            indicator_view['from_average'] = self.moving_average(from_user)
            indicator_view['to_average'] = self.moving_average(to_user)
        except ValueError:
            # Indicator doesn't support a baseline
            indicator_view['from_average'] = 0
            indicator_view['to_average'] = 0

        indicator_view['value_ticks'] = self.graph_ticks()
        indicator_view['hover_labels'] = self.graph_labels()

        indicator_view['value_labels'] = self.graph_labels()
        #indicator_view['value_labels'] = self.graph_ticks()
        indicator_view['display_type'] = self.display_type()

        return indicator_view

    def _aggregate_averages(self, answer_list, window_size=30):
        """Daily moving averages.
        The value for day x is the sum of window_size previous y answers, divided by y.

        @param answer_list Iterable of the answers to include.
        @param window_size Size in days of sliding window in which we average the values.
        @return Map key is action_date, value is aggregate average for that date
        """
        if not self.can_average():
            return []

        window = deque()
        agg_avgs = {}

        for answer in answer_list:
            if not answer.answer_num:
                continue
            
            window.append(answer.answer_num)
            if len(window) > window_size:
                window.popleft()

            agg_avgs[answer.action_date] = sum(window) / float(len(window))

        return agg_avgs

    def answers_with_average(self, from_user_or_group, to_user_or_group):
        """ Data for graphing.
        Tuple of four values, each one is a list of [date, value]:
        - from_data: From User or Group's answers to this indicator.
        - to_data: The To Users or Group's answers to this indicator.
        - from_avgs: Time average of from User or Group's answers
        - to_avgs: Time average of to User or Group's answers.
        """

        def userize(user_or_group):
            """Takes a Profile or Group and returns a Profile.
            If given a Group, returns the system user that owns that groups averages"""

            if isinstance(user_or_group, Profile):
                return user_or_group

            elif isinstance(user_or_group, Group):
                return user_or_group.avg_user

            else:
                return None

        from_user = userize(from_user_or_group)
        to_user = userize(to_user_or_group)

        my_answers_iter = Answer.objects.by_indicator(from_user, self)
        my_answers = answer_map_by_date(my_answers_iter)
                
        average_answers_iter = Answer.objects.by_indicator(to_user, self)
        average_answers = answer_map_by_date(average_answers_iter) 

        my_avgs = self._aggregate_averages(my_answers_iter)
        average_avgs = self._aggregate_averages(average_answers_iter)

        for action_date in my_answers.keys():
            # This can happen if the back-end worker fell over or is slow
            if not action_date in average_answers:
                my_ans = Answer.objects.get(
                        action_date=action_date, 
                        user=from_user, 
                        indicator_id=self.id)
                messaging.send(messaging.SUBJECT_AVG, my_ans.id)
                # No value for avg yet, so pretend avg has same value as user
                average_answers[action_date] = my_ans.num_value
                average_avgs[action_date] = my_ans.num_value

        answers = []
        for action_date, average_value in average_answers.items():
            me_value = my_answers[action_date] if action_date in my_answers else None
            my_avg = my_avgs[action_date] if action_date in my_avgs else None 
                
            answers.append(
                    (action_date, 
                    me_value, 
                    average_value, 
                    my_avg, 
                    average_avgs[action_date]
                    )
                )
         
        answers.sort(key = lambda x: x[0])    # Sort by action_date        

        me_data, average_data, me_avgs, average_avgs = [], [], [], []
        for action_date, me_value, average_value, me_avg, average_avg in answers:
            
            if me_value or me_value == 0:
                me_data.append( [action_date, me_value] )
            if average_value or average_value == 0:
                average_data.append( [action_date, average_value] )
            
            if me_avg or me_avg == 0:
                me_avgs.append( [action_date, me_avg] )
            if average_avg or average_avg == 0:
                average_avgs.append( [action_date, average_avg] )

        return (me_data, average_data, me_avgs, average_avgs)

class IndicatorLikert(Indicator):
    """Five point likert-type scale - http://en.wikipedia.org/wiki/Likert_scale"""

    # TODO: Remove this, we only have one type of Indicator, remove the whole subclass thing
    LIKERT_CHOICES = (
                         ('1', 'Never'),
                         ('2', 'Rarely'),
                         ('3', 'Sometimes'),
                         ('4', 'Often'),
                         ('5', 'Always'),
                    )

    def get_manager_url(self):
        """URL of this indicator in the admin manager"""
        return '/manager/indicator/indicatorlikert/%d/' % self.id

    def random_value(self):
        'A random value between 1 and 5'
        return random.choice( range(5) ) + 1

    def can_graph(self):
        'Can this indicator be represented on a graph?'
        return True

    def can_average(self):
        'Can an average be calculated for this indicator?'
        return True

    def as_percentage(self, num):
        "Takes the numerical value from an Answer, and returns it as a percentage"
        if not num:
            return 0
        num_choices = self.option_set.count() 
        return math.ceil( (num-1) * (100.0 / (num_choices-1)) )

    def display_type(self):
        'The type of this indicator, to select which HTML block to show'
        return 'likert'
    
    def answer_value(self, answer):
        "The value of this answer for display"
        if answer.is_skip:
            return 0
        
        likert_map = {}
        for (num, name) in IndicatorLikert.LIKERT_CHOICES:
            likert_map[num] = name
            
        try:
            display_val = likert_map[ unicode(answer.answer_num) ]
        except KeyError:
            display_val = answer.answer_num
        
        return display_val

    def graph_ticks(self):
        'Y values for the graph of this indicator'
        #return [int(x) for (x, _) in IndicatorLikert.LIKERT_CHOICES]
        return [option.position for option in self.option_set.order_by('position')]

    def graph_labels(self):
        'Y-axis labels for the graph of this indicator'
        #return [y for (_, y) in IndicatorLikert.LIKERT_CHOICES]
        return [option.value for option in self.option_set.order_by('position')]

    def graph_has_numeric_legend(self):
        """See super-class"""
        return False


class IndicatorNumber(Indicator):
    'User enters a number'
    number_range_start = models.IntegerField(null=True, help_text='Min. allowed value')
    number_range_end = models.IntegerField(null=True, help_text='Max. allowed value')
    target = models.IntegerField(blank=True, null=True,
                                 help_text='Number at which they are acheiving 100%')
    is_percentage = models.BooleanField(default=False)
    
    def get_manager_url(self):
        """URL of this indicator in the admin manager"""
        return '/manager/indicator/indicatornumber/%d/' % self.id

    def random_value(self):
        'A random value within the range for this indicator'
        end_val = 0
        if self.target:
            end_val = self.target * 2
        if not end_val or end_val > self.number_range_end:
            end_val = self.number_range_end
            
        options = range(self.number_range_start, end_val + 1)
        return random.choice(options)
    
    def can_graph(self):
        'Can this indicator be represented on a graph?'
        return True

    def can_average(self):
        'Can an average be calculated for this indicator?'
        return True

    def as_percentage(self, num):
        "Takes the numerical value from an Answer, and returns it as a percentage"
        
        if self.target:
            top_value = self.target
        else:
            top_value = self.number_range_end
        
        return min( num * (100 / top_value), 100 )  # Don't exceed 100%! 

    def display_type(self):
        'The type of this indicator, to select which HTML block to show'
        return 'number'
    
    def answer_value(self, answer):
        "The value of this answer for display"
        return answer.answer_num

    def _graph_vals(self):
        'Python array of values that go on the Y axis' 
        start = int( self.number_range_start )
 
        queryset = Answer.objects.by_indicator(get_current_user(), self)
        
        if self.is_percentage:
            end = 100
            step = 10
        else: 
            result = queryset.aggregate(models.Max('answer_num'))
            end = result['answer_num__max'] or self.number_range_end
            end = int(end)

            num_ticks = end - start
            if num_ticks >= 1000:
                step = 100
            elif num_ticks >= 500:
                step = 50
            elif num_ticks >= 150:
                step = 20
            elif num_ticks >= 100:
                step = 10
            elif num_ticks > 50:
                step = 5
            elif num_ticks > 10:
                step = 2
            else:
                step = 1

            end = end + step + 1
        
        vals = [x for x in range(start, end, step)]
        if end not in vals:    # Make sure the end value gets included
            vals.append( end )

        return vals

    def graph_ticks(self):
        'Y values for the graph of this indicator'            
        return self._graph_vals()

    def graph_labels(self):
        'Y axis labels for the graph of this indicator'
        if self.is_percentage:
            return [ str(x) +'%' for x in self._graph_vals()]
        else:
            return self.graph_ticks()


class Option(models.Model):
    """One of the choices for an Indicator"""

    indicator = models.ForeignKey(Indicator)
    value = models.CharField(max_length=250)
    position = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return self.value

    class Meta:
        """Django config"""
        ordering = ['position']

class AnswerManager(models.Manager):
    """Methods above the level of a single Answer"""

    def create_update(self, user, indicator, action_date, value, is_skip, answer=None): 
        'Creates and returns a new Answer with the given parameters, or updates the given one'
        
        is_new_answer = False

        if not answer:
            try:
                answer = self.get(
                              user = user, 
                              indicator_id = indicator.id,
                              indicator_content_type = ContentType.objects.get_for_model(indicator),
                              action_date = action_date
                              )
                
            except Answer.DoesNotExist:
                answer = Answer(user = user, 
                                action_date = action_date,
                                is_skip = is_skip)
                answer.indicator = indicator
                is_new_answer = True
        
        if is_skip:
            answer.answer_num = None
        else:
            answer.answer_num = int( value )
        
        answer.is_skip = is_skip
        answer.save()
        
        if is_new_answer:
            user.add_participation_points()
        
        try:
            Indicator.objects.next(user, indicator.campaign)
            is_last_indicator = False
        except Indicator.DoesNotExist:
            is_last_indicator = True

        if not is_skip:
            if is_last_indicator:
                # Worker won't have time before results screen comes up
                answer.update_averages()
            else:
                # Usual case, do out-of-band for performance
                messaging.send(messaging.SUBJECT_AVG, answer.id)

        return answer

    '''
    def by_day(self, user, indicator_ids, day = None):
        """Answers for the indicators whos ids are in indicator_ids of campaign for the given user and day
        @param user A Profile.
        @param campaign A Campaign.
        @param day The day to get the answers for. Defaults to yesterday.
        """
        
        if not day:
            day = user.local_datetime().date() - datetime.timedelta(1)

        answers = Answer.objects.filter(user = user, action_date = day)
        return answers
    '''

    def by_indicator(self, user, indicator):
        """Answers for ths given user and indicator for days_back until yesterday
        @param user Profile
        @param indicator Indicator
        @return Iterable of the answers.
        """

        answer_qs = Answer.objects.filter(user = user, indicator_id = indicator.id, is_skip=False)
        answer_qs = answer_qs.order_by('action_date')        
        return answer_qs


class Answer(models.Model):
    "Response to an indicator"
    
    objects = AnswerManager()
    
    # The indicator can be one of several classes
    # New-style with Option these three field will blank
    indicator_content_type = models.ForeignKey(ContentType, null=True, blank=True)
    indicator_id = models.PositiveIntegerField(null=True, blank=True)
    indicator = generic.GenericForeignKey('indicator_content_type', 'indicator_id') 

    user = models.ForeignKey(Profile)
    action_date = models.DateField(help_text='Date the behaviour happened, usually yesterday')
    
    # Averages are floating point, so this can't be an integer
    answer_num = models.FloatField(blank=True, null=True)

    is_skip = models.BooleanField(default=False, help_text='Did user skip this question?')
    created = models.DateTimeField(default=datetime.datetime.now())

    option = models.ForeignKey(Option, null=True, blank=True)

    #class Meta:
    #    """Django config"""
    #    unique_together = ('user', 'indicator_content_type', 'indicator_id', 'action_date')

    def __unicode__(self):
        #return unicode(self.user) +' for '+ unicode(self.indicator.id) +' on '+ unicode(self.action_date) +' = '+ unicode(self.value)
        return unicode(self.id)

    @property
    def value(self):
        'The answer fit for display'
        return self.indicator.answer_value(self)

    @property
    def num_value(self):
        "The answer as a number, for graphing. Returns -1 if the answer can't be converted to a num"

        return self.answer_num

    def as_percentage(self):
        'The numeric answer value as a percentage of the indicator target'
        return self.indicator.as_percentage(self.answer_num)

    def update_averages(self):
        """Updates all the averages that this Answer affects"""

        if self.is_skip:
            return

        geuser = self.user
        indicator = self.indicator
        action_date = self.action_date

        indicator.average(action_date)

        for group in geuser.groups.all():
            indicator.average(action_date, group=group)
            Indicator.objects.calculate_day_average(indicator.campaign, group.avg_user, action_date)

        Indicator.objects.calculate_day_average(indicator.campaign, geuser, action_date)

        # Update overall indicator for Avg user which is
        # the average of all users over all indicators on specific day
        avg_user = Indicator.objects.average_user()
        Indicator.objects.calculate_day_average(indicator.campaign, avg_user, action_date)

        geuser.update_compared_to_average(indicator.campaign, action_date)

