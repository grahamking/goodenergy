"""Django admin config"""

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


# ModelAdmin has lots of public methods, which upsets pylint
# pylint: disable-msg=R0904

from django.contrib import admin

from indicator.models import IndicatorLikert, IndicatorNumber, Option, Answer

class IndicatorLikertAdmin(admin.ModelAdmin):
    'Django admin config for Indicator'
    list_display = ('name', 'campaign', 'question', 'position')
    list_filter = ('campaign',)

class IndicatorNumberAdmin(admin.ModelAdmin):
    'Django admin config for Indicator'
    list_display = ('name', 'campaign', 'question', 'position')
    list_filter = ('campaign',)

class AnswerAdmin(admin.ModelAdmin):
    'Django admin config for Answer'
    list_display = ('indicator', 'user', 'action_date', 'value', 'answer_num', 'is_skip')
    list_filter = ('user', 'indicator_id')

admin.site.register(IndicatorLikert, IndicatorLikertAdmin)
admin.site.register(IndicatorNumber, IndicatorNumberAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Option)
