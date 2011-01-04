"""Tests sending HTML email
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

from django.core.management.base import NoArgsCommand
from django.core.mail import EmailMultiAlternatives
from django.template import loader, Context

class Command(NoArgsCommand):
    'Sends a test html email'
    
    help = 'Sends a test html'
    
    def handle_noargs(self, **options):             # We don't use **options so IGNORE:W0613
        'Called by NoArgsCommand'

        subject, from_email, to_email = 'Test HTML email', 'graham@gkgk.org', 'graham@gkgk.org'
        text_content = 'The text part'
        
        email_template = loader.get_template('indicator/email_input.html')
        context = Context({})
        html_content = email_template.render(context)
        
        #html_content = '<p>The <strong>html</strong> part.</p>'
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        print 'Sent'
