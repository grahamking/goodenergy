"""Django settings for goodenergy project"""

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


import os
import os.path
import logging
import logging.handlers

# TODO: Replace with Django 1.3's logging setup
def setup_logging():
    'Configure python logging'
    if not hasattr(logging, "set_up_done"):
        logging.set_up_done = False

    # settings.py gets imported multiple times, so only act on first import
    if logging.set_up_done: 
        return

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG) 

    log_filename = os.path.join(ROOT_DIR, 'goodenergy.log')
    # Rotate every 7 days, keep 4 log files
    handler = logging.handlers.TimedRotatingFileHandler(log_filename, 'D', 7, 4)

    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    logging.set_up_done = True

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# In production DEBUG should be False
#DEBUG = False
DEBUG = True

TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Graham King', 'graham@gkgk.org'),
    ('Jeremy Osborn', 'jeremy.osborn@gmail.com')
)
EMAIL_SUBJECT_PREFIX = '[Good Energy]'
DEFAULT_FROM_EMAIL = 'webmaster@goodenergy.ca'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'goodenergy',
        'USER': 'goodenergy',
        'PASSWORD': 'goodenergy',
        'HOST': '',             # Set to empty string for localhost.
        'PORT': ''             # Set to empty string for default.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Vancouver'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(ROOT_DIR, 'media/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# Use these to split media request across multiple servers. 
# By default they are both relative
#MEDIA_URL_1 = 'http://media1.goodenergy.ca/media/'
#MEDIA_URL_2 = 'http://media2.goodenergy.ca/media/'
MEDIA_URL_1 = MEDIA_URL_2 = MEDIA_URL 

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
# Use this at the command line to generate it:
# 
# python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])'
# 
# Or override it in your local_settings.py
SECRET_KEY = None

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'core.context_processor.context',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.UserMiddleware',
    'core.middleware.OrganizationMiddleware',
    'core.middleware.RefererMiddleware'
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.humanize',
    'core',
    'sorl.thumbnail',
    'compress',
    'organization',
    'campaign',
    'profile',
    'status',
    'indicator',
    'action',
    'django.contrib.admin',     # Comes last so that our templates win
    #'django.contrib.admindocs',
)

# See core.util.ge_login_required, which modifies this
LOGIN_URL = '/accounts/login/'

AUTH_PROFILE_MODULE = 'profile.Profile'

# Add our own backend so that 'django.contrib.auth.authenticate' works 
# with email addresses
AUTHENTICATION_BACKENDS = (
                           'profile.backends.EmailOrUsernameModelBackend',
                           'django.contrib.auth.backends.ModelBackend',
                           )

ONE_WEEK_SECONDS = 60 * 60 * 24 * 7
CACHE_BACKEND = 'memcached://127.0.0.1:11211/?timeout=%d' % ONE_WEEK_SECONDS

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

DEFAULT_PROFILE_PIC_URL = '/media/images/headshot_placeholder.jpg'
DEMO_PROFILE_PIC = \
        '/usr/local/goodenergy/live/app/media/images/headshot_placeholder.jpg'
GRAVATAR_DEFAULT_IMAGE = \
        'http://live.goodenergy.ca/media/images/headshot_placeholder.jpg'

# In production COMPRESS should be True
# COMPRESS = True
COMPRESS = False

COMPRESS_AUTO = True
COMPRESS_VERSION = True

COMPRESS_JS = {
    'all': {
        'source_filenames': (
                            'js/jquery.metadata.js',
                            'js/jquery.flot.js', 
                            'js/graph.js',
                            'js/jquery.normanBarChart.js',
                            'js/jquery.tools.min.js',
                            'js/jquery-ui/jquery-ui-1.8.custom.min.js',
                            'js/util.js',
                            'js/UserManager.js',
                            'js/Indicator.js',
                            'js/ActionManager.js',
                            'js/ActivityManager.js',
                            'js/Dashboard.js',
                             ),
        'output_filename': 'js/all.r?.js',
    }
}

COMPRESS_CSS = {
    'all': {
        'source_filenames': (
                            'js/jquery-ui/smoothness/jquery-ui-1.8.custom.css',
                            'css/styles.css'
                             ),
        'output_filename': 'css/all.r?.css'
    }
}

GEARMAN_SERVERS = ["127.0.0.1"]
#DAEMON_PIDFILE = os.path.join(ROOT_DIR, 'gedaemon.pid')

SHORT_URL_DOMAIN = 'http://ge1.ca/'     # Must have ending slash

#MAX_WORKER_THREADS = 10
setup_logging()

try:
    from local_settings import *    # pylint: disable-msg=W0401
except ImportError:                 # pylint: disable-msg=W0704
    pass

