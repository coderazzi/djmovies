import json
import rarfile
import re
import zipfile

from bs4 import BeautifulSoup
from html.entities import name2codepoint
from urllib.parse import urlparse, urlencode, urljoin

from movies.logic.browser import Browser
from movies.logic.dstruct import Struct

# NOTE: To prettify anything, do:
#  with open('/tmp/kk.html', 'w') as f:
#     print >> f, soup.prettify().encode('utf-8', 'ignore')

title_search = re.compile('/title/tt\d+')
duration_search = re.compile('[^\\d]*(\\d+) min.*')
IMDB_COM = 'https://www.imdb.com'
SUBTITLES_COM = 'http://www.moviesubtitles.org/'
SUBSCENE_COM = 'http://subscene.com/'
HTML_PARSER = 'lxml'

SIMULATE = False

TITLE_EXTRACTOR = re.compile('([^(]+)\(([^\)]+)\)(.*)')


def search_year(year, final_year, limit):
    start = 0
    url = 'http://www.imdb.com/search/title?at=0&sort=moviemeter,asc&start=%%d&title_type=feature&year=%s,%s' % (
        year, final_year)
    number_re = re.compile('(\d+)')
    year_match = re.compile('^\s*\(\s*(\S+?)\s*\)\s*$')
    no_spaces = re.compile('\s+', re.S)
    with Browser() as browser:
        ret = []
        while start + 1 < limit:
            page = browser.open(url % (start + 1))
            # page, limit = open('/Users/coderazzi/kk.html'), min(limit, 40)
            soup = BeautifulSoup(page.read(), HTML_PARSER)
            with open('imdb_search_year.html', 'w') as f:
                print(soup.prettify().encode('utf-8', 'ignore'), file=f)
            table = soup.find('table', attrs={'class': 'results'})
            for g1 in soup.find_all('div', attrs={'class': 'lister-item'}):
                g2 = g1.find('div', attrs={'class': 'lister-item-image'})
                if g2:
                    a = g2.find('a')
                    if a:
                        href = urlparse(a.get('href')).path
                        img = a.find('img')
                        if img:
                            title, img = img.get('alt'), img.get('loadlate')
                            rating = g1.find('div', attrs={'class': 'ratings-imdb-rating'})
                            rating = rating.get('data-value') if rating else '?'
                            start = g1.find('span', attrs={'class': 'lister-item-index'})
                            match = start and number_re.search(start.text)
                            if match:
                                start = int(match.group(1))
                                if start > limit:
                                    break
                                info = g1.find_all('p')  # , attrs={'class': 'text-muted'})
                                if len(info) == 4:
                                    genre = info[0].find('span', attrs={'class': 'genre'})
                                    genre = genre.text.strip() if genre else '?'
                                    outline = no_spaces.sub(' ', _unescape(info[1].text), )
                                    credit = no_spaces.sub(' ', _unescape(info[2].text), )
                                    year = g1.find('span', attrs={'class': 'lister-item-year'})
                                    year = year and year_match.match(year.text)
                                    search = '%s %s' % (title, year.group(1)) if year else title
                                    ret.append((href, title, img, rating, start, outline, credit, genre, search))
        return ret


def search_imdb(movie_title):
    with Browser() as browser:
        ret = []
        # small trick, for cases when we cannot find the movie by name: we can enter the URL directly (at imdb)
        if movie_title.startswith(IMDB_COM):
            href = urlparse(movie_title).path
            info = _get_imdb_info(get_uid(href, ''), browser)
            if info:
                uid = get_uid(href, info.title)
                info.uid = uid
                ret.append((uid, info.title, info.year))
                return ret, info

        # http://www.imdb.com/search/title?count=250&title=last%20stand&title_type=feature,tv_movie&view=simple
        movie_title = movie_title.replace('.', ' ')
        if SIMULATE:
            with open('/tmp/imdb_search.html') as f:
                soup = BeautifulSoup(f.read(), HTML_PARSER)
        else:
            url = IMDB_COM + '/find?' + urlencode({'q': movie_title})
            print(url)
            # url = IMDB_COM + '/search/title?' + urlencode(
            #     {'count': '50', 'title_type': 'feature,tv_movie', 'title': movieTitle, 'view': 'simple'})
            # note that count could be up to 250
            soup = BeautifulSoup(browser.open(url).read(), HTML_PARSER)
            with open('/tmp/imdb_search.html', 'w') as f:
                print(soup.prettify().encode('utf-8', 'ignore'), file=f)
        section = soup.find(class_='findList')
        if section:
            first, ref, image = True, None, None
            for td in section.find_all('td'):
                # first td wraps the image and link
                # second gets the title
                if first:
                    first = False
                    aref = td.find('a')
                    if aref:
                        ref, image = urlparse(aref.get('href')).path, aref.find('img').get('src')
                else:
                    first = True
                    # second td is <td class="result_text"> <a href="/title/tt2953050/?ref_=fn_al_tt_1">Encanto</a> (2021) </td>
                    # for some reason, there are \n characters (like '\', 'n')
                    text = _unescape(td.text.replace('\\n',' ').strip())
                    match = TITLE_EXTRACTOR.match(text)
                    if match:
                        year = match.group(2)
                        title, extra = match.group(1).strip(),match.group(3).strip()
                        if extra:
                            title = title + ' ' + extra
                        ret.append((get_uid(ref, title), title, year))
        return ret, ret and _get_imdb_info(ret[0][0], browser)


def search_imdb_basic(movie_title):
    """ Not used any longer, would return movies in incorrect language"""

    ret = []
    url = IMDB_COM + '/find?' + urlencode({'q': movie_title, 's': 'all'})
    with Browser() as browser:
        page = browser.open(url)
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        div_main = soup.find('div', attrs={'id': 'main'})
        if div_main:
            t_search = re.compile('/title/tt\d+')
            for td in div_main.find_all('td'):
                ref = td.find('a')
                if ref:
                    href = ref.get('href')
                    if href and t_search.match(href):
                        href = urlparse(href).path  # we remove any parameters information. So far, is useless
                        title = _unescape(ref.text)
                        if title:
                            ret.append((get_uid(href, title), title, _unescape(ref.nextSibling)))
        return ret, ret and _get_imdb_info(ret[0][0], browser)


def get_uid(href, title):
    # when we retrieve movies by name (searchImdb), we obtain a list of URLs, and the associated title.
    # However, when visiting those URLs, the retrieved title could have a different value (normally due
    # to some translation). For this reason, we encode the url and the title in a single uid
    return href + ' ' + title


def get_imdb_info(link):
    with Browser() as browser:
        return _get_imdb_info(link, browser)


def _get_imdb_info(uid, browser):
    # the link includes, in fact, the URL, a space, and the title
    title, year, duration, genres, actors, trailer, img_src, big_img_src = [None] * 8
    link, title = uid.split(' ', 1)
    page = browser.open(IMDB_COM + link)
    # page = open('imdb.html')
    soup = BeautifulSoup(page.read(), HTML_PARSER)
    with open('imdb.html', 'w') as f:
        print(soup.prettify().encode('utf-8', 'ignore'), file=f)

    data = json.loads(soup.find('script', type='application/ld+json').text)
    title = data['name']
    try:
        year = data['datePublished'].split('-')[0]
    except:
        year = '???'
    genres = '/'.join(data['genre'])
    actors = '/'.join([x['name'] for x in data['actor']])
    try:
        trailer = data['trailer']['embedUrl']
    except KeyError:
        trailer = ''
    img_src = data['image']
    # duration
    for infoBar in soup.findAll('time'):
        match = duration_search.match(_unescape(infoBar.text))
        duration = match and match.group(1)
        if duration:
            break
    if not duration:
        print('Attention, no duration!!!!')
    url = urlparse(link).path  # we remove any parameters information. So far, is useless
    return Struct.nonulls(url=url, title=title, year=year, duration=duration, uid=uid,
                          genres=genres, actors=actors, trailer=trailer, imageLink=img_src, bigImageLink=big_img_src)


def _unescape(text):
    # By Fredrik Lundh (http://effbot.org/zone/re-sub.htm#_unescape-html)
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return chr(int(text[3:-1], 16))
                else:
                    return chr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = chr(name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text.strip()  # leave as is

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
            pass  # responds with 500 error, always
        soup = BeautifulSoup(browser.response().read(), HTML_PARSER)
        ret = []
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            if pattern.match(href):
                ret.append((_unescape(tag.text), href))
        return ret


def getSubtitles(subTitleRef, language, firstSubtitle, lastSubtitle):
    ret, url = {}, SUBTITLES_COM
    with Browser() as browser:
        page = browser.open(urljoin(url, subTitleRef))
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        subrefs = []
        for each in soup.find_all('a', attrs={'title': 'Download %s subtitles' % language.lower()}):
            # tr=each.parent
            # while tr and tr.name != "table": 
            #     tr=tr.parent
            # parts=tr and tr.find('td', attrs={'title':'parts'})
            parts = each.parent.find('td', attrs={'title': 'parts'})
            if parts and parts.text == '1':
                subrefs.append(each['href'])
        subtitleIdx = 1
        for each in subrefs:
            page = browser.open(urljoin(url, each))
            soup = BeautifulSoup(page.read(), HTML_PARSER)
            img = soup.find('img', attrs={'title': 'Download'})
            if img:
                ref = img.parent.parent.parent
                ref = ref and ref.get('href')
                if ref:
                    subtitleIdx += 1
                    if subtitleIdx > firstSubtitle:
                        f = browser.retrieve(urljoin(url, ref))
                        with zipfile.ZipFile(f[0]) as z:
                            names = z.namelist()
                            for i in range(len(names)):
                                name = names[i]
                                if name.lower().endswith('.srt'):
                                    content = z.read(name)
                                    try:
                                        content = content.decode('iso-8859-1').encode('utf8')
                                    except:
                                        pass
                                    ret[name] = content
                        if subtitleIdx == lastSubtitle:
                            break
    return ret


def searchSubtitlesOnSubscene(movieTitle):
    pattern = re.compile('.*/movie-(?:[^\.]+).htm.*')
    with Browser() as browser:
        browser.open(SUBSCENE_COM)
        browser.select_form(nr=0)
        browser.form['query'] = movieTitle
        try:
            browser.submit()
        except:
            pass  # responds with 500 error, always
        soup = BeautifulSoup(browser.response().read(), HTML_PARSER)
        ret, included = [], set()
        for prio, group in [(0, 'exact'), (1, 'popular'), (1, 'close')]:
            header = soup.find('h2', attrs={'class': group})
            if header:
                for ul in header.fetchNextSiblings()[:1]:
                    for tag in ul.find_all('a', href=True):
                        href = tag['href']
                        if href not in included:
                            ret.append([prio, _unescape(tag.text), href])
                            included.add(href)
        ret.sort()
        return [(b, c) for a, b, c in ret]


def getSubtitlesOnSubscene(subTitleRef, language, firstSubtitle, lastSubtitle):
    ret, url = {}, SUBSCENE_COM
    with Browser() as browser:
        page = browser.open(urljoin(url, subTitleRef))
        soup = BeautifulSoup(page.read(), HTML_PARSER)
        subrefs = []
        for each in soup.find_all('td', attrs={'class': 'a1'}):
            span = each.find('span')
            if span and _unescape(span.text) == language:
                ref = each.find('a')
                ref = ref and ref.get('href')
                if ref: subrefs.append(ref)
        # firstSubtitle, lastSubtitles are 1 based
        for each in subrefs[firstSubtitle - 1:lastSubtitle]:
            try:
                page = browser.open(urljoin(url, each))
            except Exception as ex:
                print('Error retrieving ref ' + each, ex)
                continue
            soup = BeautifulSoup(page.read(), HTML_PARSER)
            ref = soup.find('a', attrs={'id': 'downloadButton'})
            ref = ref and ref.get('href')
            if ref:
                try:
                    f = browser.retrieve(urljoin(url, ref))
                except Exception as ex:
                    print('Error retrieving ref ' + ref, ex)
                    continue
                type = f[1].getsubtype()
                if type == 'x-zip-compressed':
                    handler = zipfile.ZipFile
                elif type == 'x-rar-compressed':
                    handler = rarfile.RarFile
                else:
                    print('getSubtitlesOnSubscene: Received file of type ' + type + ", discarded")
                    continue
                try:
                    with handler(f[0]) as z:
                        names = z.namelist()
                        single = None
                        for i in range(len(names)):
                            name = names[i]
                            if name.lower().endswith('.srt'):
                                if single:
                                    print('getSubtitlesOnSubscene: Received multiple scrs, discarded')
                                    break
                                single = name
                        else:
                            if single:
                                print('getSubtitlesOnSubscene: reading on ' + type + ' entry ' + single)
                                content = z.read(single)
                                try:
                                    content = content.decode('iso-8859-1').encode('utf8')
                                except:
                                    pass
                                ret[single] = content
                            else:
                                print('getSubtitlesOnSubscene: Received no  scrs, discarded')
                except:
                    print('getSubtitlesOnSubscene: Error reading file ' + ref)
                    pass
    return ret