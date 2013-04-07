import htmlentitydefs, os, re, urllib, urllib2

from BeautifulSoup import BeautifulSoup

from browser import Browser
from dstruct import Struct


title_search = re.compile('/title/tt\d+')
duration_search = re.compile('[^\\d]*(\\d+) min.*')

def searchImdb(movieTitle):
    ret=[]
    url='http://www.imdb.com/find?'+urllib.urlencode({'q': movieTitle, 's':'all'})
    with Browser() as browser:
        page = browser.open(url)
        soup = BeautifulSoup(page.read())
        divMain = soup.find('div', attrs={'id':'main'})
        if divMain:
            title_search = re.compile('/title/tt\d+')    
            for td in divMain.findAll('td'):
                ref=td.find('a')
                if ref:
                    href=ref.get('href')
                    if href and title_search.match(href):
                        title = _unescape(ref.text)
                        if title:
                            ret.append(('http://www.imdb.com'+href,title, _unescape(ref.nextSibling)))
        return (ret, ret and _getImdbInfo(ret[0][0], browser))


def getImdbInfo(link):
    with Browser() as browser:
        return _getImdbInfo(link, browser)

def _getImdbInfo(link, browser):
    title, year, duration, genres, actors, trailer, imgSrc, bigImgSrc = [None]*8
    page = browser.open(link)
    soup = BeautifulSoup(page.read())
    divMain = soup.find('div', attrs={'id':'pagecontent'})
    if divMain:
        #title and year
        titleTag=divMain.find('h1', attrs={'class':'header'})
        if titleTag:
            yearRef = titleTag.find('a')
            if yearRef:
                year = _unescape(yearRef.text)
            else:
                yearRef = titleTag.find('span', attrs={'class':'nobr'})
                match = yearRef and re.search('(\d\d\d\d)', _unescape(yearRef.text))
                year = match and match.group(1)
            titleTag = titleTag.find('span', attrs={'itemprop':'name'})
            if titleTag:
                title = _unescape(titleTag.contents[0])
        #duration
        infoBar = divMain.find('div', attrs={'class':'infobar'})
        if infoBar:
            match = duration_search.match(_unescape(infoBar.text))
            duration = match and match.group(1)
        #actors, genres
        genres='/'.join([_unescape(each.text) for each in divMain.findAll('span',itemprop='genre')])
        starsInfo = divMain.find('div', attrs={'itemprop':'actors'})
        if starsInfo:
            actors='/'.join([_unescape(each.text) for each in starsInfo.findAll('span',itemprop='name')])
        trailer = divMain.find('a', itemprop='trailer')
        trailer = trailer and trailer.get('href')
        #image now
        tdImg = divMain.find('td', attrs={'id':'img_primary'})
        if tdImg:
            imgTag = tdImg.find('img')
            imgSrc = imgTag and imgTag.get('src')
            if imgSrc:
                bigImgSrc = imgTag.parent.get('href')
                if bigImgSrc:
                    try:
                        imgTag = BeautifulSoup(browser.open(bigImgSrc).read()).find('img', attrs={'id' : 'primary-img'})
                        bigImgSrc = imgTag and imgTag.get('src')
                    except:
                        bigImgSrc=None
        return Struct.nonulls(url=link, title=title, year=year, duration=duration, 
            genres=genres, actors=actors, trailer=trailer, imageLink=imgSrc, bigImageLink=bigImgSrc)


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
        return text.strip() # leave as is
    if not text: return ''
    return re.sub("&#?\w+;", fixup, text).strip()

