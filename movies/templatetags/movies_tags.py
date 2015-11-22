import urllib

from django.core.urlresolvers import reverse
from django.template import Library

register=Library()

# @register.simple_tag
# def usenet_search(search):
# 	url='https://www.binsearch.info/index.php?%s&m=&max=25&adv_g=&adv_age=999&adv_sort=date&adv_nfo=on&minsize=8000&maxsize=24000&font=&postdate='
# 	param = urllib.urlencode({'q':search.encode('utf-8', 'ignore')})
# 	return url % param

@register.simple_tag
def uquery_search(search):
	return reverse('#create_query')+'?'+urllib.urlencode({'q':search.encode('utf-8', 'ignore')})
