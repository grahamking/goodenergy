"""Django forms for campaign app.
This are Python representations of HTML forms.
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



from django import forms

from campaign.models import Campaign
from indicator.models import Indicator

class CampaignForm(forms.ModelForm):

    class Meta:
        exclude = ['organization']
        model = Campaign

    def __init__(self, organization, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)

        self.organization = organization

    def save(self, commit=True):
        'Write to database'

        is_new = not self.instance.id  # Gets set by superclass save

        campaign = super(CampaignForm, self).save(commit=False)
        campaign.organization = self.organization
        if commit:
            campaign.save()

        if is_new:
            Indicator.objects.create_overall_indicator(campaign)
 
        return campaign

