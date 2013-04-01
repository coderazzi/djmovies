import htmlentitydefs
import os
import re
import urllib
import urllib2

from BeautifulSoup import BeautifulSoup
from mechanize import Browser
from dstruct import Struct

title_search = re.compile('/title/tt\d+')
duration_search = re.compile('[^\\d]*(\\d+) min.*')

def unescape(text):
    # By Fredrik Lundh (http://effbot.org/zone/re-sub.htm#unescape-html)
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


def getBrowser():
    br = Browser()
    br.addheaders = [
        ('User-agent', 
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
        ('Accept-Language',
            'en-US,en;q=0.8')]
    return br


def getImdbReferences(movieTitle):
    ret=[]
    url='http://www.imdb.com/find?'+urllib.urlencode({'q': movieTitle, 's':'all'})
    browser=getBrowser()
    try:
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
                        title = unescape(ref.text)
                        if title:
                            ret.append(('http://www.imdb.com'+href,title, unescape(ref.nextSibling)))
    finally:
        browser.close()
    return ret


def getBasicImdbInfo(link):
    browser=getBrowser()
    try:
        return _getFullImdbInfo(browser, link)
    finally:
        browser.close()

def getImdbInfo(link):
    browser=getBrowser()
    try:
        ret = _getFullImdbInfo(browser, link)
        if ret:
            try:
                if ret.imageLink:
                    ret.img = browser.open_novisit(ret.imageLink).read()
                    ret.imgType=os.path.splitext(ret.imageLink)[-1]
                if ret.bigImageLink:
                    ret.bigImg = browser.open(ret.bigImageLink).read()
                    ret.bigImgType=os.path.splitext(ret.bigImageLink)[-1]
            except urllib2.HTTPError:
                pass
        return ret
    finally:
        browser.close()

def _getFullImdbInfo(browser, link):
    title, year, duration, genres, actors, trailer, imgSrc, bigImgSrc = [None]*8
    page = browser.open(link)
    soup = BeautifulSoup(page.read())
    divMain = soup.find('div', attrs={'id':'pagecontent'})
    if divMain:
        #title and year
        titleTag=divMain.find('h1', attrs={'class':'header'})
        if titleTag:
            yearRef = titleTag.find('a')
            year = yearRef and unescape(yearRef.text)
            titleTag = titleTag.find('span', attrs={'itemprop':'name'})
            if titleTag:
                title = unescape(titleTag.contents[0])
        #duration
        infoBar = divMain.find('div', attrs={'class':'infobar'})
        if infoBar:
            match = duration_search.match(unescape(infoBar.text))
            duration = match and match.group(1)
        #actors, genres
        genres='/'.join([unescape(each.text) for each in divMain.findAll('span',itemprop='genre')])
        starsInfo = divMain.find('div', attrs={'itemprop':'actors'})
        if starsInfo:
            actors='/'.join([unescape(each.text) for each in starsInfo.findAll('span',itemprop='name')])
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
                    imgTag = BeautifulSoup(browser.open(bigImgSrc).read()).find('img', attrs={'id' : 'primary-img'})
                    bigImgSrc = imgTag and imgTag.get('src')
        return Struct(title=title, year=year, duration=duration, 
            genres=genres, actors=actors, trailer=trailer, imageLink=imgSrc, bigImageLink=bigImgSrc)


# with open('/Users/coderazzi/development/tmp/example.html') as f:
#     html=f.read()
# #print html
# soup = BeautifulSoup(html)
# divMain = soup.find('div', attrs={'id':'pagecontent'})
# if divMain:
#     titleTag=divMain.find('h1', attrs={'class':'header'})
#     yearRef = titleTag.find('a')
#     year = yearRef and unescape(yearRef.text)
#     print year
#     a=  titleTag.find('span', attrs={'itemprop':'name'})
#     print unescape(a.contents[0])
#     infoBar = divMain.find('div', attrs={'class':'infobar'})
#     if infoBar:
#         match = duration_search.match(unescape(infoBar.text))
#         print match and match.group(1)
#     genres='/'.join([unescape(each.text) for each in divMain.findAll('span',itemprop='genre')])
#     starsInfo = divMain.find('div', attrs={'itemprop':'actors'})
#     if starsInfo:
#         actors='/'.join([unescape(each.text) for each in starsInfo.findAll('span',itemprop='name')])
#     trailer = divMain.find('a', itemprop='trailer')
#     trailer = trailer and trailer.get('href')

#     print genres
#     print actors
#     print trailer
