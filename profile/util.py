"""Utilities for the profile module.
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


import urllib
import Image

from core import gravatar

IMAGE_MAX_SIDE = 800
def save_picture(geuser, django_file):
    'Write picture to disk, resizing very large images as we go'
    
    ext = django_file.name[-3:]
    
    pic_name = geuser.profile_pic_filename(abspath=True, ext=ext, variant='full')
    relative_pic_name = geuser.profile_pic_filename(abspath=False, ext=ext, variant='full')

    destination = open(pic_name, 'wb+')
    for chunk in django_file.chunks():
        destination.write(chunk)
    destination.close()

    # Resize big images
    image = Image.open(pic_name)
    (width, height) = image.size
    if max(width, height) > IMAGE_MAX_SIDE:

        if width > height:
            aspect_ratio = float(width) / float(height)
            width = IMAGE_MAX_SIDE
            height = IMAGE_MAX_SIDE / aspect_ratio
        else:
            aspect_ratio = float(height) / float(width)
            height = IMAGE_MAX_SIDE
            width = IMAGE_MAX_SIDE / aspect_ratio
        
        resized = image.resize( (width, height) )
        resized.save(pic_name)    

    return relative_pic_name

def save_gravatar(geuser):
    'Fetches and saves users gravatar'

    pic_name = geuser.profile_pic_filename(abspath=True, ext='jpg', variant='full')
    relative_pic_name = geuser.profile_pic_filename(abspath=False, ext='jpg', variant='full')

    url = gravatar.for_email(geuser.user.email, size=288)
    urllib.urlretrieve(url, pic_name)

    return relative_pic_name

