import htmlentitydefs, os, re, urllib, urllib2, urlparse, zipfile, rarfile

from bs4 import BeautifulSoup

from browser import Browser
from dstruct import Struct

#NOTE: To prettify anything, do:
#  with open('/tmp/kk.html', 'w') as f:
#     print >> f, soup.prettify().encode('utf-8', 'ignore')

title_search = re.compile('/title/tt\d+')
duration_search = re.compile('[^\\d]*(\\d+) min.*')
IMDB_COM='http://www.imdb.com'
SUBTITLES_COM='http://www.moviesubtitles.org/'
SUBSCENE_COM='http://www.subscene.com/'
HTML_PARSER='lxml'


def searchYear(year, finalYear, limit):
    start = 0
    showYear = year!=finalYear
    url='http://www.imdb.com/search/title?at=0&sort=moviemeter,asc&start=%%d&title_type=feature&year=%s,%s' % (year, finalYear)
    numberRe = re.compile('(\d+)')    
    yearInTitle=re.compile('^\s*(.*?)\s+\((\d\d\d\d)\)\s*$')
    noSpaces=re.compile('\s+', re.S)
    with Browser() as browser:
        ret=[]
        while start+1<limit:
            page = browser.open(url % (start+1))
            #page, limit = open('/Users/coderazzi/kk.html'), min(limit, 40)
            soup = BeautifulSoup(page.read(), HTML_PARSER)
            table = soup.find('table', attrs={'class' : 'results'})
            for tr in table.find_all('tr'):                
                number = tr.find('td', attrs={'class' : 'number'})
                match = number and numberRe.search(number.text)
                if match:
                    start = int(match.group(1))
                    if start>limit:
                        break
                    imageTd = tr.find('td', attrs={'class' : 'image'})
                    imageTd = imageTd and imageTd.find('a')
                    if imageTd:
                        href=urlparse.urlparse(imageTd.get('href')).path
                        title = search = imageTd.get('title')
                        idx = yearInTitle.match(title)
                        if idx:
                            matchTitle, matchYear = idx.group(1), idx.group(2)
                            search = '%s %s' % (matchTitle, matchYear)
                            if not showYear:
                                title = matchTitle
                        title=_unescape(title)
                        search = urllib.urlencode({'q':search.encode('utf-8', 'ignore')})
                        image=imageTd.find('img')
                        image = image and image.get('src')
                        try:
                            rating = tr.find('span', attrs={'class' : 'rating-rating'}).find('span', attrs={'class' : 'value'}).text.strip()
                        except:
                            rating = '???'
                        outline=tr.find('span', attrs={'class':'outline'})
                        outline = outline and outline.text.strip()
                        credit=tr.find('span', attrs={'class':'credit'})
                        credit = credit and noSpaces.sub(' ', _unescape(credit.text),)
                        genre=tr.find('span', attrs={'class':'genre'})
                        genre = genre and noSpaces.sub(' ', _unescape(genre.text),)
                        ret.append((href, title, image, rating, start, outline, credit, genre, search))
        return ret

def searchImdb(movieTitle):
    with Browser() as browser:
        ret=[]
        #small trick, for cases when we cannot find the movie by name: we can enter the URL directly (at imdb)
        if movieTitle.startswith(IMDB_COM):
            #href=movieTitle[len(IMDB_COM):]
            href=urlparse.urlparse(movieTitle).path
            info = _getImdbInfo(getUid(href,''), browser)
            if info:
                uid=getUid(href, info.title)
                info.uid=uid
                ret.append((uid, info.title, info.year))
                return (ret, info)

        #http://www.imdb.com/search/title?count=250&title=last%20stand&title_type=feature,tv_movie&view=simple
        url=IMDB_COM+'/search/title?'+urllib.urlencode({'count': '50', 'title_type':'feature,tv_movie', 'title': movieTitle, 'view':'simple'})
        #note that count could be up to 250
        page = browser.open(url)
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        for td in soup.find_all('td', attrs={'class':'title'}):
            ref=td.find('a')
            if ref:
                href=urlparse.urlparse(ref.get('href')).path #we remove any parameters information. So far, is useless
                title = _unescape(ref.text)
                if title:
                    ret.append((getUid(href, title),title, _unescape(ref.nextSibling))) #this is the year
        return (ret, ret and _getImdbInfo(ret[0][0], browser))

def searchImdbBasic(movieTitle):
    '''Not used any longer, would return movies in incorrect language'''
    ret=[]
    url=IMDB_COM+'/find?'+urllib.urlencode({'q': movieTitle, 's':'all'})
    with Browser() as browser:
        page = browser.open(url)
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        divMain = soup.find('div', attrs={'id':'main'})
        if divMain:
            title_search = re.compile('/title/tt\d+')    
            for td in divMain.find_all('td'):
                ref=td.find('a')
                if ref:
                    href=ref.get('href')
                    if href and title_search.match(href):
                        href=urlparse.urlparse(href).path #we remove any parameters information. So far, is useless
                        title = _unescape(ref.text)
                        if title:
                            ret.append((getUid(href, title), title, _unescape(ref.nextSibling)))
        return (ret, ret and _getImdbInfo(ret[0][0], browser))

def getUid(href, title):
    #when we retrieve movies by name (searchImdb), we obtain a list of URLs, and the associated title.
    #However, when visiting those URLs, the retrieved title could have a different value (normally due
    # to some translation). For this reason, we encode the url and the title in a single uid
    return href+' '+title

def getImdbInfo(link):
    with Browser() as browser:
        return _getImdbInfo(link, browser)

def _getImdbInfo(uid, browser):
    #the link includes, in fact, the URL, an space, and the title
    title, year, duration, genres, actors, trailer, imgSrc, bigImgSrc = [None]*8
    link, title = uid.split(' ', 1)
    page = browser.open(IMDB_COM+link)
    soup = BeautifulSoup(page.read(), HTML_PARSER)
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
            if not title:
                titleTag = titleTag.find('span', attrs={'itemprop':'name'})
                if titleTag:
                    title = _unescape(titleTag.contents[0])
        #duration
        infoBar = divMain.find('div', attrs={'class':'infobar'})
        if infoBar:
            match = duration_search.match(_unescape(infoBar.text))
            duration = match and match.group(1)
        #actors, genres
        genres='/'.join([_unescape(each.text) for each in divMain.find_all('span',itemprop='genre')])
        starsInfo = divMain.find('div', attrs={'itemprop':'actors'})
        if starsInfo:
            actors='/'.join([_unescape(each.text) for each in starsInfo.find_all('span',itemprop='name')])
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
                        imgTag = BeautifulSoup(browser.open(bigImgSrc).read(), HTML_PARSER).find('img', attrs={'id' : 'primary-img'})
                        bigImgSrc = imgTag and imgTag.get('src')
                    except:
                        bigImgSrc=None
        url=urlparse.urlparse(link).path #we remove any parameters information. So far, is useless
        return Struct.nonulls(url=url, title=title, year=year, duration=duration, uid=uid,
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


def searchSubtitles(movieTitle):
    pattern = re.compile('.*/movie-(?:[^\.]+).htm.*')
    with Browser() as browser:
        browser.open(SUBTITLES_COM)
        browser.select_form(nr=0)
        browser.form['q'] = movieTitle
        try:
            browser.submit()
        except:
            pass #responds with 500 error, always
        soup = BeautifulSoup(browser.response().read(), HTML_PARSER)
        ret=[]
        for tag in soup.find_all('a', href=True):
            href=tag['href']
            if pattern.match(href):
                ret.append((_unescape(tag.text), href))
        return ret


def getSubtitles(subTitleRef, language, firstSubtitle, lastSubtitle):
    ret, url ={}, SUBTITLES_COM
    with Browser() as browser:
        page = browser.open(urlparse.urljoin(url, subTitleRef))
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        subrefs=[]
        for each in soup.find_all('a', attrs={'title':'Download %s subtitles' % language.lower()}):
            # tr=each.parent
            # while tr and tr.name != "table": 
            #     tr=tr.parent
            # parts=tr and tr.find('td', attrs={'title':'parts'})
            parts=each.parent.find('td', attrs={'title':'parts'})
            if parts and parts.text=='1':
                subrefs.append(each['href'])
        subtitleIdx=1
        for each in subrefs:
            page = browser.open(urlparse.urljoin(url, each))
            soup = BeautifulSoup(page.read(), HTML_PARSER)
            img = soup.find('img', attrs={'title':'Download'})
            if img:
                ref=img.parent.parent.parent
                ref=ref and ref.get('href')
                if ref:
                    subtitleIdx+=1
                    if subtitleIdx>firstSubtitle:
                        f = browser.retrieve(urlparse.urljoin(url, ref))
                        with zipfile.ZipFile(f[0]) as z:
                            names = z.namelist()
                            for i in range(len(names)):
                                name=names[i]
                                if name.lower().endswith('.srt'):
                                    content=z.read(name)
                                    try:
                                        content=content.decode('iso-8859-1').encode('utf8')
                                    except:
                                        pass
                                    ret[name]=content
                        if subtitleIdx==lastSubtitle:
                            break
    return ret


def searchSubtitlesOnSubscene(movieTitle):
    pattern = re.compile('.*/movie-(?:[^\.]+).htm.*')
    with Browser() as browser:
        browser.open(SUBSCENE_COM)
        browser.select_form(nr=0)
        browser.form['q'] = movieTitle
        try:
            browser.submit()
        except:
            pass #responds with 500 error, always
        soup = BeautifulSoup(browser.response().read(), HTML_PARSER)
        ret, included=[], set()
        for prio, group in [(0, 'exact'), (1, 'popular'), (1, 'close')]:
            header=soup.find('h2', attrs={'class': group})
            if header:
                for ul in header.fetchNextSiblings()[:1]:
                    for tag in ul.find_all('a', href=True):
                         href=tag['href']
                         if href not in included:
                            ret.append([prio, _unescape(tag.text), href])
                            included.add(href)
        ret.sort()
        return [(b, c) for a, b, c in ret]

import time
def getSubtitlesOnSubscene(subTitleRef, language, firstSubtitle, lastSubtitle):
    ret, url = {}, SUBSCENE_COM
    with Browser() as browser:
        page = browser.open(urlparse.urljoin(url, subTitleRef))
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        subrefs=[]
        for each in soup.find_all('td', attrs={'class':'a1'}):
            span=each.find('span')
            if span and _unescape(span.text)==language:
                ref=each.find('a')
                ref=ref and ref.get('href')                
                if ref: subrefs.append(ref)
        #firstSubtitle, lastSubtitles are 1 based
        for each in subrefs[firstSubtitle-1:lastSubtitle]:
            try:
                page = browser.open(urlparse.urljoin(url, each))
            except Exception, ex:
                print 'Error retrieving ref '+each, ex
                continue
            soup = BeautifulSoup(page.read(), HTML_PARSER)
            ref=soup.find('a', attrs={'id': 'downloadButton'})
            ref=ref and ref.get('href')
            if ref:
                try:
                    f = browser.retrieve(urlparse.urljoin(url, ref))
                except Exception, ex:
                    print 'Error retrieving ref '+ref, ex
                    continue
                type=f[1].getsubtype()
                if type=='x-zip-compressed':
                    handler=zipfile.ZipFile
                elif type=='x-rar-compressed':
                    handler=rarfile.RarFile
                else:
                    print 'getSubtitlesOnSubscene: Received file of type '+type+", discarded"
                    continue
                with handler(f[0]) as z:
                    names = z.namelist()
                    single = None
                    for i in range(len(names)):
                        name=names[i]
                        if name.lower().endswith('.srt'):
                            if single:
                                print 'getSubtitlesOnSubscene: Received multiple scrs, discarded'
                                break
                            single = name
                    else:
                        if single:
                            print 'getSubtitlesOnSubscene: reading on '+type+' entry '+single
                            content=z.read(single)
                            try:
                                content=content.decode('iso-8859-1').encode('utf8')
                            except:
                                pass
                            ret[single]=content                
                        else:
                            print 'getSubtitlesOnSubscene: Received no  scrs, discarded'
    return ret



#print getSubtitlesOnSubscene(searchSubtitlesOnSubscene('The Rock')[0][1], 'English')
