import sys
import os

# Virtual env
sys.path = ['/home/graham/.virtualenvs/goodenergy/lib/python2.6/site-packages'] + sys.path
# The app
sys.path.append('/usr/local/goodenergy/live/app')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

