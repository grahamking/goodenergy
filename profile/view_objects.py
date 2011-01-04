"""Representation of profile module objects for the view
Allows us to pre-calculate things, that we can't do in the model object.
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


class ProfileView(object):
    """View representation of a Profile"""

    def __init__(self, profile):

        self.id = profile.id
        self.username = profile.user.username
        self.name = profile.user.get_full_name()

        self.profile_pic_url = profile.pic_url()
        self.about = profile.about

        self.participation_points = profile.participation_points 
        self.inspiration_points = profile.inspiration_points
        self.inspiration_points_credit = profile.inspiration_points_credit

    def __unicode__(self):
        return self.name

