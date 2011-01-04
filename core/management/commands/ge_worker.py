""" Worker daemon for Good Energy. Runs in the background, connected via Gearman,
and does long running tasks.
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


# Disable the pylint check for dynamically added attributes. This happens a lot
# with Django DB model usage.
# pylint: disable-msg=E1101
# pylint: disable-msg=E1103

import logging
import time
import random
import threading

import daemon
from gearman import GearmanWorker
from django.conf import settings    # Sets up logging
from django.db import connection, transaction
from django.core.management.base import NoArgsCommand

from core import messaging
from indicator.models import Indicator, Answer


class GEWorker(daemon.Daemon):
    "Our worker daemon - takes Gearman jobs and does them"
    
    def __init__(self):
        super(GEWorker, self).__init__()
        self.worker = GearmanWorker(settings.GEARMAN_SERVERS)

        self.worker.register_function(messaging.SUBJECT_THREAD_COUNT, self.thread_count)
        self.worker.register_function(messaging.SUBJECT_THREAD_NAMES, self.thread_names)

        self.worker.register_function(messaging.SUBJECT_AVG, self.average)

        self._set_transaction_isolation()

    def _set_transaction_isolation(self):
        """ 
        Defaut transaction isolation on MySQL InnoDB is REPEATABLE-READ, which means
        a connection always gets the same result for a given query, even if the data has
        changed.
        This daemon runs for a long time, we need to see db changes, so change to READ-COMMITTED.
        """
        
        cur = connection.cursor()
        cur.execute("set session transaction isolation level read committed")
        cur.close()

    def run(self):
        """Entry point for daemon.Daemon subclasses - main method"""
        self.worker.work()  # Never returns
    
    def wait_for_thread(self):
        'Sleeps until a thread is available. Gearman will queue the requests whilst we pause here'
        
        if settings.DEBUG:
            connection.queries = [] # Prevent query list growing indefinitely 

        running_threads = threading.active_count() 
        while running_threads >= settings.MAX_WORKER_THREADS:
            logging.debug(
                    'Waiting for thread. Currently %s: %s' % 
                    (running_threads, self.thread_names()) )
            time.sleep(1)
    
    def thread_count(self, job):
        'Returns number of threads currently running'
        return str(threading.active_count()) +'\n'

    def thread_names(self, job):
        'Returns an array of active thread names'
        return str( ', '.join([thread.name for thread in threading.enumerate()]) ) +'\n'
    
    def average(self, job):
        """ Calculates daily indicator average for group and overall
        @job.arg Id of the new Answer to include. 
        """
        self.wait_for_thread()
        worker_thread = AverageWorker(job.arg)
        worker_thread.start()

 
class Command(NoArgsCommand):
    'Starts a worker daemon'
    
    help = 'Starts a worker daemon'
    
    def handle_noargs(self, **options):
        """Django Command main method"""
        logging.debug('Starting worker')
        try:
            GEWorker().main(settings.DAEMON_PIDFILE)
        except Exception:
            logging.exception("Fatal error")


class AverageWorker(threading.Thread):
    'Calculates group and overall averages'

    def __init__(self, arg):
        thread_name = self.__class__.__name__ + str( random.randint(0, 10000) )
        super(AverageWorker, self).__init__(name = thread_name)

        self.answer_id = arg
        logging.debug('AverageWorker: Answer Id %s' % self.answer_id)

    def run(self):
        'Main'
        logging.debug('Running AverageWorker')

        try:
            answer = Answer.objects.get(pk = self.answer_id)
        except Answer.DoesNotExist:
            logging.warn('No Answer with id %s' % self.answer_id)
            return

        answer.update_averages()

        transaction.commit_unless_managed()

