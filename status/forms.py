"""Django forms for status module."""

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

from status.models import EntryComment


class CommentForm(forms.ModelForm):
    """Django form to add a comment on a status update"""

    def __init__(self, *args, **kwargs):
        self.geuser = kwargs.pop('user')
        self.entry = kwargs.pop('entry')
        super(CommentForm, self).__init__(*args, **kwargs)
    
    class Meta:         # Doesn't need an __init__ IGNORE:W0232
        model = EntryComment
        exclude = ('user', 'created', 'entry')

    def save(self, *args, **kwargs):
        'Write to the database'
        
        comment = super(CommentForm, self).save(commit=False)
        comment.user = self.geuser
        comment.entry = self.entry
        
        comment.save()
        self.entry.update_comment_count()
        #self.geuser.add_participation_points()
        
        return comment
