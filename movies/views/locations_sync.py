import json
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from movies.models import Location, MovieLocation

from local.locations import LocationHandler
from local.imdb import getImdbImages


SUPPORT_GET_FOR_TESTING=True

def index(request):    
    if not SUPPORT_GET_FOR_TESTING:
        if request.method == 'GET': return redirect('#locations')
        locationId, locationPath = request.POST['location.id'], request.POST['location.path']
    else:
        if request.method == 'GET': 
            locationId, locationPath = 1, u'/Volumes/TTC7/_movies/test'
        else:
            locationId, locationPath = request.POST['location.id'], request.POST['location.path']


    movies= {}
    location = Location.objects.get(id=locationId)
    for each in MovieLocation.objects.filter(location=location):
        movies[each.path]=[each.movie.title, True]

    for path, ok in LocationHandler(locationPath).iterateAllFilesInPath():
        if ok:
            info = movies.get(path)
            if info:
                info[1]=False
            else:
                movies[path]=['', False]
        else:
            messages.warning(request, 'Cannot access path: '+path)
    
    info=[]
    for key in sorted(movies.keys(), key=unicode.lower):
        movie=movies[key]
        info.append((key, movie[0], movie[1]))

    return render_to_response('locations_sync.html', 
        {      
            'location' : location,
            'path'     : locationPath,
            'movies'   : info,
        },
        RequestContext(request))


def update(request):
    if request.method == 'GET': return redirect('#locations')
    data = json.loads(request.body)
    filepath, mediainfo, imdbinfo = data['filepath'], data['mediainfo'], data['imdbinfo']
    location, dirpath = data['location'], data['dirpath']

    images = getImdbImages(imdbinfo.imageLink, imdbinfo.bigImageLink)

    path = locationHandler = LocationHandler(dirpath).renameFile(filepath)

    print filepath
    print mediainfo
    print imdbinfo
    print location
    print dirpath


            # imdbInfo= getImdbInfo(self.browser, references[index-1][0])
            # if not imdbInfo.year:
            #     imdbInfo.year = raw_input("Year not returned by IMDB, please enter it: ").strip()
            # newName = self.normalizeFilename(imdbInfo.title, path, imdbInfo.year)           
            # if newName != path:
            #     print '***I***', 'renaming', path,'as', newName
            #     os.rename(path, newName)
            # locationName = self._getRelativeName(folder, newName)
            # self.db.storeMovie(mInfo, imdbInfo, self.location, locationName)
            # self.db.commit()


    # def normalizeFilename(self, title, basePath, year):
    #     year = (year and ('__'+year)) or ''
    #     basename=re.sub('[^a-z0-9]+', '_', title.lower()).title()
    #     return os.path.join(os.path.dirname(basePath), basename+year+os.path.splitext(basePath)[-1].lower())

    # def _getRelativeName(self, basepath, path):
    #     ret = path[len(basepath):]
    #     if ret[0]=='/':
    #         ret=ret[1:]
    #     return ret

