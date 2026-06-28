from django import template
import urllib.parse
register = template.Library()

@register.filter
def urlencode(value):
    return urllib.parse.quote(str(value))
