"""Wrapper around our message queue
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


from threading import Thread
import logging

from gearman.libgearman import Client
from django.conf import settings

SUBJECT_AVG = 'average'

CLIENT = Client()
for host in settings.GEARMAN_SERVERS:
    CLIENT.add_server(host)


def send(subject, payload):
    """Send a message. Subject must be one of the constants in this file. 
    Payload will be converted to a string"""
    CLIENT.do_background(subject, str(payload))


def delayed_send(subject, payload, seconds_delay):
    """Calls send in seconds_delay"""
    logging.debug('Scheduling send for in %d seconds', seconds_delay)
    delay = DelayThread(subject, payload, seconds_delay)
    delay.start()
    

class DelayThread(Thread):
    """A thread that sleeps for a given amount of time, 
    then calls send with the correct info"""
    
    def __init__(self, subject, payload, seconds_delay):
        super(DelayThread, self).__init__()
        self.subject = subject
        self.payload = payload
        self.seconds_delay = seconds_delay
        
    def run(self):
        'Thread main loop'
        import time
        logging.debug('Thread sleeping')
        time.sleep(self.seconds_delay)
        logging.debug('Thread woke up')
        send(self.subject, self.payload)
