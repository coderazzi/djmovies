import htmlentitydefs
import rarfile
import re
import urllib
import urlparse
import zipfile

from bs4 import BeautifulSoup


# NOTE: To prettify anything, do:
#  with open('/tmp/kk.html', 'w') as f:
#     print >> f, soup.prettify().encode('utf-8', 'ignore')

title_search = re.compile('/title/tt\d+')
duration_search = re.compile('[^\\d]*(\\d+) min.*')
IMDB_COM = 'http://www.imdb.com'
SUBTITLES_COM = 'http://www.moviesubtitles.org/'
SUBSCENE_COM = 'http://subscene.com/'
HTML_PARSER = 'lxml'

limit = 300
def _unescape(text):
    # By Fredrik Lundh (http://effbot.org/zone/re-sub.htm#_unescape-html)
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text.strip()  # leave as is

    if not text: return ''
    return re.sub("&#?\w+;", fixup, text).strip()

numberRe = re.compile('(\d+)')
yearMatch = re.compile('^\s*\(\s*(\S+?)\s*\)\s*$')
noSpaces = re.compile('\s+', re.S)
with open('../../imdb_search_year.html', 'r') as f:
    soup = BeautifulSoup(f.read(), HTML_PARSER)
    for g1 in soup.find_all('div', attrs={'class' : 'lister-item'}):
        g2 = g1.find('div', attrs={'class': 'lister-item-image'})
        if g2:
            a = g2.find('a')
            if a:
                href = urlparse.urlparse(a.get('href')).path
                img = a.find('img')
                if img:
                    title, img = img.get('alt'), img.get('loadlate')
                    rating = g1.find('div', attrs={'class': 'ratings-imdb-rating'})
                    rating = rating.get('data-value') if rating else '?'
                    start = g1.find('span', attrs={'class': 'lister-item-index'})
                    match = start and numberRe.search(start.text)
                    if match:
                        start = int(match.group(1))
                        if start > limit:
                            break
                        info = g1.find_all('p')#, attrs={'class': 'text-muted'})
                        print 1
                        if len(info) == 4:
                            genre = info[0].find('span', attrs={'class': 'genre'})
                            genre = genre.text.strip() if genre else '?'
                            outline = noSpaces.sub(' ', _unescape(info[1].text), )
                            credit = noSpaces.sub(' ', _unescape(info[2].text), )
                            year = g1.find('span', attrs={'class': 'lister-item-year'})
                            year = year and yearMatch.match(year.text)
                            search = '%s %s' % (title, year.group(1)) if year else title
                            print href, title, img, rating, start#, outline, credit, genre, search

