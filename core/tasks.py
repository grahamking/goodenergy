""" Worker daemon for Good Energy. 
Runs in the background via oilcan, connected via Gearman,
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

from oilcan import task
from django.db import connection, transaction

from indicator.models import Answer


def _set_transaction_isolation():
    """ 
    Defaut transaction isolation on MySQL InnoDB is 
    REPEATABLE-READ, which means a connection always gets 
    the same result for a given query, even if the data has changed.
    This daemon runs for a long time, we need to see db changes, 
    so change to READ-COMMITTED.
    """
    
    cur = connection.cursor()
    cur.execute("set session transaction isolation level read committed")
    cur.close()


@task
def average(answer_id_str):
    """ Calculates daily indicator average for group and overall.
    @answer_id_str: Id of the new Answer to include. String.
    """
    logging.debug('Running AverageWorker')
    _set_transaction_isolation()
    answer_id = long(answer_id_str)

    try:
        answer = Answer.objects.get(pk=answer_id)
    except Answer.DoesNotExist:
        logging.warn('No Answer with id %s', answer_id)
        return

    answer.update_averages()

    transaction.commit_unless_managed()

