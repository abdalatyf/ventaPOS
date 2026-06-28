from django import template
from salesapp.utils import to_arabic_numerals

register = template.Library()

@register.filter(name='to_arabic')
def to_arabic_filter(value):
    return to_arabic_numerals(value)