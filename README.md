Good Energy is a behavior change and employee engagement tool. It uses key results from social psychology research (social norms, pledges, identity) to assist individuals in achieving their goals. It has been deployed in production with the David Suzuki Foundation, focused on environmental sustainability, and with a Vancouver area school, focused on student self-improvement.

Good Energy was designed as a white-label product. The company purchasing it brands the header, footer, and CSS to look like their site. It then looks integrated into either a company Intranet, or a public Internet.

The questions you get asked (top center), as well as the default Pledges (bottom right) are configurable via the django admin interface.

WARNING: Good Energy is currently [abandon-ware](http://en.wikipedia.org/wiki/Abandonware). You could probably hire the original developers (https://github.com/grahamking or https://github.com/jeremydosborn) to assist in a deployment, and with behavior change consulting, but there's no offical support for it, and we're both pretty busy.

You should have at least basic Django, Unix, and database skills before trying to set up this app. As long as you understand that, and you need a behavior change / employee engagement tool, we think you'll really like Good Energy.

Good Energy is free software, licensed under the [GNU Affero General Public License](http://www.gnu.org/licenses/agpl.html).

# Installation

### Get Dependencies:

The obvious stuff:

  - Python 2.6+
  - Django 1.3+ 
  - A Django supported database. Tested with MySQL and Postgres.
  - Memcached and it's python lib (See: http://docs.djangoproject.com/en/dev/topics/cache/#memcached). Memcached is not optional.

Python libs:

  - pytz: http://pytz.sourceforge.net/ (Ubuntu package: **python-tz**)
  - Python Imaging Library (PIL): http://effbot.org/zone/pil-index.htm (Ubuntu package: **python-imaging**)

Django apps:

  - sorl.thumbnail: http://thumbnail.sorl.net/ (**pip install sorl-thumbnail**)
  - django-compress: http://code.google.com/p/django-compress/ (Checkout source and _python setup.py install_)

For the back-end worker (optional):

  - Gearman: http://gearman.org/ (Ubuntu package: **gearman-job-server**)
  - python-libgearman: http://pypi.python.org/pypi/python-libgearman/ (Ubuntu package: **python-gearman.libgearman**)
  - oilcan: http://github.com/grahamking/oilcan (See README at that url)

### Generate SECRET_KEY.

Run this command:

    python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz123456790!@#$%^&*(-_=+)") for i in range(50)])'

and in settings.py assign the result to SECRET_KEY (around line 122).

### Create and init database, tweaks settings

Create a database and user (suggested name: _goodenergy_).

MySQL:
    CREATE DATABASE goodenergy CHARACTER SET utf8 collate utf8_general_ci;
    GRANT ALL ON goodenergy.* TO goodenergy@localhost IDENTIFIED BY 'goodenergy';

Postgres:
    CREATE DATABASE goodenergy ENCODING 'utf8';
    CREATE USER goodenergy SUPERUSER;
    ALTER USER goodenergy WITH PASSWORD 'goodenergy';

If you didn't use 'goodenergy' for the database, user, and password, change settings.py to reflect that.

That should be enough to run the dev server. For live you'll need to tweak the file paths in settings.py. You can override any settings with a local_settings.py file in the same directory as settings.py.

Initialize the databse:

    ./manage.py syncdb

That creates a sample campaign for you to play with.

# Business objects

The top level concept in Good Energy is an Organization. Each company using or deploying Good Energy is an Organization, and they typically have their own url.

Each Organization runs Campaigns. A Campaign is a set of questions (indicator.Indicator), status updates (status.Entry), and pledges (action.Action).

A Campaign can start and end on fixed dates, or can start when the user joins and run for a given amount of time. Outside of the demo, most campaigns are fixed dates. It takes about a month for a new habit to form, and people bore easily, so we suggest running campaigns for 5 weeks as a good compromise. Typically the organisation will advertise the campaign ahead of time, and choosing a significant date to start (Earth Day, for example), helps people remember to join.

An Indicator is a question that gets asked each time users return to the site. Indicators are all multiple choice, the choices are indicator.Option objects. Each users answer is recorded as an indicator.Answer.

You'll notice IndicatorLikert and IndicatorNumber as descendants of Indicator. You should use IndicatorLikert for everthing. IndicatorNumber is only for calculating averages internally.

Internal averages use a system user and a system indicator (OVERALL).

Status updates (status.Entry) can have comments (status.EntryComment).

A pledge (action.Pledge) is when someone pledges to perform a given action (action.Action). Other users can comment on action (action.Comment), or mention what is blocking them from performing said action (action.Barrier).


