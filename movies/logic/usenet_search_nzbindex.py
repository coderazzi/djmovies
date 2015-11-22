import re, urllib
from bs4 import BeautifulSoup
from datetime import date, timedelta
from movies.logic.browser import Browser
from movies.logic.dstruct import Struct

# NOTE: To prettify anything, do:
#  with open('/tmp/kk.html') as i:
#     soup = BeautifulSoup(i.read(), HTML_PARSER)
#  with open('/tmp/kk_output.html', 'w') as f:
#     print >> f, soup.prettify().encode('utf-8', 'ignore')

HTML_PARSER = 'lxml'
SEARCH = 'http://www.nzbindex.nl/search/?q=%s&sort=agedesc&minsize=%d&maxsize=%d&max=%d&more=1&hidespam=1&p=%d'
MAX_RESULTS=25
MIN_SIZE = 4567

BROWSER = Browser()

def search_title(title, min_size, max_size, exclude_oid_list=None, stop_on_oid=None):
    """Searchs in usenet for the given title, using the specific min_size
       If exclude_oid_list, the return list will not include any download with the
       given oids.
       If stop_on_oid is specified, the method stops as soon as the given oid is found
       It returns the newest oid (download id) found, and the list of results, sorted from newer to older"""
    if exclude_oid_list is None:
        exclude_oid_list = []
    title_ext = re.compile('"([^"]+)"',re.M | re.S)
    parts_reg = re.compile("^[^\(]+\((\d+).*$", re.M | re.S)
    nfo_reg = re.compile("^javascript:nfo\('([^']+)'\);$",re.M | re.S)
    files_reg = re.compile("^((\s+\d+\s*\w+\s+\|?)+).*$", re.M|re.S)
    size_reg = re.compile('([\d\.]+).([GM])')
    time_reg = re.compile('^\s+([\d\.]+)\s+(\w+)\s+', re.M|re.S)
    ret, exclude_list = [], exclude_oid_list[:]
    search_init, loop, agreed, first_oid_found = 0, True, False, None
    today = date.today()
    while loop:
        loop = False
        BROWSER.open(_search_url(title, min_size, max_size, MAX_RESULTS, search_init))
        soup = BeautifulSoup(BROWSER.response().read(), HTML_PARSER)
        #soup = BeautifulSoup(open('example_output_nzb_index.html').read(), HTML_PARSER)

        with open('nzb_index_trace.html', 'w') as f:
            print >> f, soup.prettify().encode('utf-8', 'ignore')

        if not search_init:
            form = soup.find('form')
            if form and 'agree' in form.get('action'):
                if agreed:
                    raise 'We need to agreed, but is already done!'
                agreed = True
                BROWSER.select_form(nr=0)
                BROWSER.submit()
                continue

        search_init += 1

        area = soup.find('form', attrs={'action': 'http://www.nzbindex.nl/download/'})
        if not area:
            break
        area = area.find('tbody')
        assert area, 'No tbody found'
        for tr in area.find_all('tr'):
            tds = tr.find_all('td')
            if tds:
                inp = tds[0].find('input', attrs={'type': 'checkbox'})
                if inp:
                    oid = inp['value']
                    if first_oid_found is None:
                        first_oid_found = oid
                    if oid == stop_on_oid:
                        return first_oid_found, ret
                    if oid in exclude_list:
                        continue
                    loop = True
                    exclude_list.append(oid)
                    if tds[1].find('span', attrs={'class': 'threat'}):
                        continue #Password protected
                    for a in tds[1].find_all('a'):
                        if a.text == 'Download':
                            download = a.get('href')
                    desc = tds[1].find('label')
                    if desc:
                        match = title_ext.search(''.join(desc.text.split()))
                        if match:
                            parts = 1
                            desc = match.group(1)
                            info = tds[1].find('span', attrs={'class': 'complete'})
                            if info:
                                match = parts_reg.match(info.text)
                                if match:
                                    parts = int(match.group(1))
                            total_parts = parts
                            info = tds[1].find('div', attrs={'class': 'fileinfo'})
                            nfo, files = None, None
                            if info:
                                files = files_reg.match(info.text)
                                if files:
                                    files = files.group(1).strip().lower()
                                nfo = info.find('a')
                                if nfo:
                                    nfo = nfo.get('href')
                                    if nfo:
                                        match = nfo_reg.match(nfo)
                                        if match:
                                            nfo = _get_nfo(match.group(1))
                            if not files:
                                files='?'
                            match = size_reg.match(tds[2].text.strip().replace(',',''))
                            if match:
                                size = float(match.group(1))
                                if match.group(2) == 'G':
                                    size *= 1000
                            else:
                                size = 0
                            if size < min_size:
                                continue
                            match = time_reg.match(tds[4].text)
                            time = today
                            if match:
                                reference = float(match.group(1))
                                if match.group(2)[0]=='d':
                                    reference *= 24
                                time -= timedelta(hours=int(reference))
                            ret.append(Struct(oid=oid, desc=desc, size=int(size),
                                              nfo=nfo, files=files, since=time.strftime('%Y-%m-%d'),
                                              parts=parts, total_parts=total_parts, download=download))
    return first_oid_found, ret


def _get_nfo(ref):
    BROWSER.open(ref)
    soup = BeautifulSoup(BROWSER.response().read(), HTML_PARSER)
    # soup = BeautifulSoup(open('example_output_nzb_index_nfo.html.html').read(), HTML_PARSER)
    # with open('example_output_nzb_index_nfo.html.html', 'w') as f:
    #     print >> f, soup.prettify().encode('utf-8', 'ignore')
    # return
    body = soup.find('pre', attrs={'id': 'nfo0'})
    if body:
        ret = body.text.strip()
        if ret != 'PAR2':
            return ret


def _search_url(title, min_size, max_size, max_results, first):
    return SEARCH % (urllib.quote_plus(title), min_size, max_size, max_results, first)

