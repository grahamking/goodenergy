# Installation

### Get Dependencies:

The obvious stuff:
    - Django 1.3+. 
    - A Django supported database. Tested with MySQL and Postgres.
    - Memcached

Django apps:
    - sorl.thumbnail: http://thumbnail.sorl.net/
    - django-compress: http://code.google.com/p/django-compress/

### Tweak settings.py

Put in your database details, file paths, and so on. 
You can override any settings with a local_settings.py file
in the same directory as settings.py.

### Generate SECRET_KEY.

Run this command:

    python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz123456790!@#$%^&*(-_=+)") for i in range(50)])'

and in settings.py assign the result to SECRET_KEY (around line 122).

### Init database

A sample campaign is created via Django's fixtures when you syncdb:

    ./manage.py syncdb

