"""Django forms for Indicators"""

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
import re

from django import forms
from django.utils.safestring import mark_safe
from django.utils import dateformat

from indicator.models import IndicatorLikert, Answer

TO_COMMA_RE = '^.*?,'

def indicator_form(*args, **kwargs):
    'Creates and returns the appropriate django form for the given indicator'

    indicator = kwargs['indicator']

    form_class_name = indicator.__class__.__name__ +'Form'
    form_class = eval(form_class_name)

    return form_class(*args, **kwargs)


class AbstractIndicatorForm(forms.Form):
    """Superclass of all indicator forms"""

    skip = forms.CharField(max_length=1, widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        
        self.indicator = kwargs.pop('indicator')
        self.user = kwargs.pop('user')

        self.previous = kwargs.pop('previous', None)
        self.answer = kwargs.pop('instance', None)
 
        if self.previous:
            date_str = 'Since '+ dateformat.format(self.previous.action_date, 'l F jS') +','
            self.indicator.question = re.sub(TO_COMMA_RE, date_str, self.indicator.question)

        super(AbstractIndicatorForm, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.indicator.question

    def show_previous(self):
        'Should we display the "Previously you said" box?'
        return True

    def save(self):
        "Write to the database"
        
        try:
            answer_val = self.cleaned_data['answer']
        except KeyError:    # User didn't answer that question, nothing to do
            answer_val = 0
        
        is_skip = self.cleaned_data['skip'] == '1'
        
        yesterday = self.user.local_datetime().date() - datetime.timedelta(1)
       
        return Answer.objects.create_update(
                self.user,
                self.indicator,
                yesterday,
                answer_val,
                is_skip,
                answer = self.answer
                )


class IndicatorLikertForm(AbstractIndicatorForm):
    'Form for likert indicators'

    answer = forms.ChoiceField(choices=IndicatorLikert.LIKERT_CHOICES,
                               widget=forms.RadioSelect(),
                               label='',
                               required=False)
    
'''    
class IndicatorMultipleChoiceForm(AbstractIndicatorForm):
    'Form for multiple choice indicators'
    
    def __init__(self, *args, **kwargs):
        super(IndicatorMultipleChoiceForm, self).__init__(*args, **kwargs)
        
        choices = []
        i = 0
        for option in self.indicator.multiple_choice.splitlines():
            choices.append( (i, option) )
            i += 1
            
        self.fields['answer'] = forms.ChoiceField( choices=choices,
                                                   widget=forms.RadioSelect(),
                                                   label='',
                                                   required=False )
'''

class IndicatorNumberForm(AbstractIndicatorForm):
    'Form for numerical indicators'
    
    def __init__(self, *args, **kwargs):
        super(IndicatorNumberForm, self).__init__(*args, **kwargs)
    
        self.fields['answer'] = forms.IntegerField(self.indicator.number_range_end,
                                                   self.indicator.number_range_start,
                                                   required=False)

    def as_ul(self):
        'Display as HTML - called by the template to render this form'
        form_html = super(IndicatorNumberForm, self).as_ul()
        if self.indicator.target:
            form_html += u'<li class="target">Target: '+ unicode(self.indicator.target) +u'</li>'
        return mark_safe(form_html)


INDICATOR_TYPE_CHOICES = (
    ('IndicatorLikert', 'Likert'),
    ('IndicatorNumber', 'Numeric')
)

class IndicatorCreateEditForm(forms.Form):
    'Form to create a new indicator or edit an existing one'

    position = forms.IntegerField()
    name = forms.CharField()
    question = forms.CharField()
    description = forms.CharField(widget=forms.Textarea())
    type = forms.ChoiceField(choices = INDICATOR_TYPE_CHOICES)

    number_range_start = forms.IntegerField(required = False, help_text='Numeric indicators only')
    number_range_end = forms.IntegerField(required = False, help_text='Numeric indicators only')
    target = forms.IntegerField(required = False, help_text='Numeric indicators only')

    def __init__(self, campaign, *args, **kwargs):

        instance = None
        if 'instance' in kwargs:
            instance = kwargs.pop('instance')

        super(IndicatorCreateEditForm, self).__init__(*args, **kwargs)

        self.campaign = campaign

        self.id = None
        if instance:
            instance = instance.subclass()
            self.id = instance.id

            self.fields['type'].initial = instance.__class__.__name__
            self.fields['type'].widget.attrs['disabled'] = 'disabled'

            self.fields['position'].initial = instance.position
            self.fields['name'].initial = instance.name
            self.fields['question'].initial = instance.question
            self.fields['description'].initial = instance.description

            if hasattr(instance, 'number_range_start'):
                self.fields['number_range_start'].initial = instance.number_range_start
                self.fields['number_range_end'].initial = instance.number_range_end
                self.fields['target'].initial = instance.target 
            else:
                self.fields['number_range_start'].widget.attrs['disabled'] = 'disabled'
                self.fields['number_range_end'].widget.attrs['disabled'] = 'disabled'
                self.fields['target'].widget.attrs['disabled'] = 'disabled'

    def save(self):
        'Write to the database'
        classname = self.cleaned_data['type']
        class_ = eval(classname)  # TODO: Security risk!

        if self.id:
            ind = class_.objects.get(pk = self.id)
            ind.position = self.cleaned_data['position']
            ind.name = self.cleaned_data['name']
            ind.question = self.cleaned_data['question']
            ind.description = self.cleaned_data['description']
        else:
            ind = class_(
                position = self.cleaned_data['position'],
                name = self.cleaned_data['name'],
                question = self.cleaned_data['question'],
                description = self.cleaned_data['description'],
                campaign = self.campaign
                )

        if classname == 'IndicatorNumber':
            ind.number_range_start = self.cleaned_data['number_range_start']
            ind.number_range_end = self.cleaned_data['number_range_end']
            ind.target = self.cleaned_data['target']

        ind.save()
        return ind

