import htmlentitydefs, os, re, urllib, urllib2, urlparse, zipfile

from BeautifulSoup import BeautifulSoup

from browser import Browser
from dstruct import Struct


title_search = re.compile('/title/tt\d+')
duration_search = re.compile('[^\\d]*(\\d+) min.*')
IMDB_COM='http://www.imdb.com'
SUBTITLES_COM='http://www.moviesubtitles.org/'

def searchImdb(movieTitle):
    ret=[]
    #http://www.imdb.com/search/title?count=250&title=last%20stand&title_type=feature,tv_movie&view=simple
    url=IMDB_COM+'/search/title?'+urllib.urlencode({'count': '50', 'title_type':'feature,tv_movie', 'title': movieTitle, 'view':'simple'})
    #note that count could be up to 250
    with Browser() as browser:
        page = browser.open(url)
        soup = BeautifulSoup(page.read())
        for td in soup.findAll('td', attrs={'class':'title'}):
            ref=td.find('a')
            if ref:
                href=urlparse.urlparse(ref.get('href')).path #we remove any parameters information. So far, is useless
                title = _unescape(ref.text)
                if title:
                    ret.append((href,title, _unescape(ref.nextSibling))) #this is the year
        return (ret, ret and _getImdbInfo(ret[0][0], browser))

def searchImdbBasic(movieTitle):
    '''Not used any longer, would return movies in incorrect language'''
    ret=[]
    url=IMDB_COM+'/find?'+urllib.urlencode({'q': movieTitle, 's':'all'})
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
                        href=urlparse.urlparse(href).path #we remove any parameters information. So far, is useless
                        title = _unescape(ref.text)
                        if title:
                            ret.append((href,title, _unescape(ref.nextSibling)))
        return (ret, ret and _getImdbInfo(ret[0][0], browser))


def getImdbInfo(link):
    with Browser() as browser:
        return _getImdbInfo(link, browser)

def _getImdbInfo(link, browser):
    title, year, duration, genres, actors, trailer, imgSrc, bigImgSrc = [None]*8
    page = browser.open(IMDB_COM+link)
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
        url=urlparse.urlparse(link).path #we remove any parameters information. So far, is useless
        return Struct.nonulls(url=url, title=title, year=year, duration=duration, 
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


def getSubtitles(movieTitle, year, language):
    ret, url, title=[], SUBTITLES_COM, unicode('%s (%s)' % (movieTitle, year))
    with Browser() as browser:
        browser.open(url)
        browser.select_form(nr=0)
        browser.form['q'] = movieTitle
        try:
            browser.submit()
        except:
            pass #responds with 500 error, always
        soup = BeautifulSoup(browser.response().read())
        for tag in soup.findAll('a', href=True):
            if title == _unescape(tag.text):
                page = browser.open(urlparse.urljoin(url, tag['href']))
                soup = BeautifulSoup(page.read())
                subrefs=[]
                for each in soup.findAll('a', attrs={'title':'Download %s subtitles' % language.lower()}):
                    parts=each.parent.find('td', attrs={'title':'parts'})
                    if parts and parts.text=='1':
                        subrefs.append(each['href'])
                for each in subrefs:
                    page = browser.open(urlparse.urljoin(url, each))
                    soup = BeautifulSoup(page.read())
                    img = soup.find('img', attrs={'title':'Download'})
                    if img:
                        ref=img.parent.parent.parent
                        ref=ref and ref.get('href')
                        if ref:
                            f = browser.retrieve(urlparse.urljoin(url, ref))
                            with zipfile.ZipFile(f[0]) as z:
                                names = z.namelist()
                                if len(names)==1:
                                    ret.append(z.read(names[0]))
                break
    return ret


#print getSubtitles('American Gangster', '2007', 'Spanish')