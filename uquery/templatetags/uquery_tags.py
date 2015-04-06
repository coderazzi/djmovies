import time, urllib

from django.template import Library

register=Library()

@register.simple_tag
def format_time(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(seconds))

@register.simple_tag
def format_day(seconds):
    return time.strftime("%Y-%m-%d", time.localtime(seconds))

@register.simple_tag
def urllib_quote(str):
    return urllib.quote(str)

@register.filter
def is_recent(seconds):
    '''Returns True if is recent (1 day old max)'''
    return time.time()-seconds<86400

@register.filter
def size_unit(size):
    '''Returns True if is recent (1 day old max)'''
    return min(4, int(size/4000))
