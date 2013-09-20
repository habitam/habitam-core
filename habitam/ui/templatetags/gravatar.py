'''
This file is part of Habitam.

Habitam is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as 
published by the Free Software Foundation, either version 3 of 
the License, or (at your option) any later version.

Habitam is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License along with Habitam. If not, see 
<http://www.gnu.org/licenses/>.
    
Created on Apr 20, 2013

@author: Stefan Guna

Based on http://en.gravatar.com/site/implement/images/django/
'''
from django import template
from django.contrib.sites.models import Site
from django.templatetags.static import static
import hashlib
import urllib
 
register = template.Library()
 
class GravatarUrlNode(template.Node):
    def __init__(self, email):
        self.email = template.Variable(email)
 
    def render(self, context):
        try:
            email = self.email.resolve(context)
        except template.VariableDoesNotExist:
            return ''
 
        current_site = Site.objects.get_current()
        default = current_site.domain + static('ui/img/habitam-worker-user.png')
        size = 80
 
        gravatar_url = "https://secure.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default, 's':str(size)})
 
        return gravatar_url
 
@register.tag
def gravatar_url(parser, token):
    try:
        tag_name, email = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires a single argument" % token.contents.split()[0]
 
    return GravatarUrlNode(email)