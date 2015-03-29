import re, urllib

from bs4 import BeautifulSoup
from datetime import date, timedelta

from local.browser import Browser

class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)


#NOTE: To prettify anything, do:
#  with open('/tmp/kk.html') as i:
#     soup = BeautifulSoup(i.read(), HTML_PARSER)
#  with open('/tmp/kk_output.html', 'w') as f:
#     print >> f, soup.prettify().encode('utf-8', 'ignore')

HTML_PARSER='lxml'
SEARCH='https://www.binsearch.info/index.php?q=%s&max=25&min=%d&adv_age=1999&adv_sort=date&minsize=%d&maxsize=%d'
NFO_MARK='view NFO'
NFO_SEARCH='https://www.binsearch.info/viewNFO.php?oid=%d'

def search_title(title, min_size, max_size, exclude_oid_list=[], stop_on_oid=None):
    '''Searchs in usenet for the given title, using the specific min_size
       If exclude_oid_list, the return list will not include any download with the
       given oids.
       If stop_on_oid is specified, the method stops as soon as the given oid is found
       It returns the newest oid (download id) found, and the list of results, sorted from newer to older'''
    pattern=re.compile('.*?size: ([\d\.]+).([GM])B, parts available: (\d+) / (\d+)(.*)$')
    info_pattern=re.compile('\s*-\s*')
    number=re.compile('\s*(\d+)\.\s*')
    ret, exclude_list=[], exclude_oid_list[:]
    first_oid_found, search_init, loop = None, 0, True
    with Browser() as browser:
        while loop:
            browser.open(_search_url(title, min_size, max_size, search_init))
            soup = BeautifulSoup(browser.response().read(), HTML_PARSER)        
            #soup = BeautifulSoup(open('../kk.html').read(), HTML_PARSER)        
            area = soup.find('table', attrs={'id': 'r2'})
            if not area:
                break
            today=date.today()
            for tr in area.find_all('tr'):
                tds=tr.find_all('td')
                if tds and len(tds)>1:
                    order=tds[0].text
                    # if len(tds)<2:
                    #     with open('/tmp/usenet_search.txt', 'w') as f:
                    #         print >> f, soup.prettify().encode('utf-8', 'ignore')
                    inp=tds[1].find('input', attrs={'type': 'checkbox'})
                    if inp:
                        oid=int(inp['name'])       
                        #print 'Obtained oid=',oid            
                        if first_oid_found is None:
                            first_oid_found=oid
                        if oid==stop_on_oid:
                            return first_oid_found, ret 
                        if oid in exclude_list:
                            continue
                        exclude_list.append(oid)
                        desc=tds[2].find('span', attrs={'class': 's'}).text
                        info=tds[2].find('span', attrs={'class': 'd'})
                        if info:
                            match=pattern.match(info.text)
                            if match:                            
                                parts, total_parts, rest=int(match.group(3)), int(match.group(4)), match.group(5)
                                if 'requires password' in rest:
                                    continue
                                nfo = rest.endswith(NFO_MARK)
                                if nfo:
                                    rest=rest[:-len(NFO_MARK)]
                                    nfo=_get_nfo(browser, oid)
                                else:
                                    nfo=None
                                rest='\n'.join(info_pattern.split(rest[2:]))
                                size=float(match.group(1))
                                if match.group(2)=='G':
                                    size*=1000
                                time, reference=today, tds[5].text.strip()
                                if reference[-1]=='d':
                                    time-=timedelta(days=int(reference[:-1]))
                                ret.append(Struct(oid=oid, desc=desc, size=int(size), 
                                    nfo=nfo, files=rest, since=time.strftime('%Y-%m-%d'), 
                                    parts=parts, total_parts=total_parts))
            loop=False
            menu=soup.find_all('table', attrs={'class': 'xMenuT'})
            if len(menu)==2:
                td = menu[1].find('td')
                if td:
                    for link in td.find_all('a'):
                        if link.text=='>':
                            match=number.match(order)
                            if match:
                                loop=True
                                search_init=int(match.group(1))
                            break
        return first_oid_found, ret


def _get_nfo(browser, oid):
    browser.open(NFO_SEARCH%(oid))
    soup = BeautifulSoup(browser.response().read(), HTML_PARSER)      
    #soup = BeautifulSoup(open('../kk2.html').read(), HTML_PARSER)        
    body = soup.find('body')
    assert body, 'No body found!!'
    ret=body.text.strip()
    return None if ret=='PAR2' else ret



def _search_url(title, min_size, max_size, first):
    return SEARCH%(urllib.quote_plus(title), first, min_size, max_size)



# with open('../kk.html') as i:
#     soup = BeautifulSoup(i.read(), HTML_PARSER)
# with open('../kk_output.html', 'w') as f:
#     print >> f, soup.prettify().encode('utf-8', 'ignore')
