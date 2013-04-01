import re
import os

class LocationHandler:

    def __init__(self, folderBase):
        self.folderBase=folderBase

    def isValid(self):
        return os.path.isdir(self.folderBase)

    def iterateAllFilesInPath(self):
        stack=[self.folderBase]
        while stack:
            current = stack.pop()
            if os.path.isdir(current):
                try:
                    subs = os.listdir(current)
                except OSError:
                    yield current, False
                    continue
                if not 'VIDEO_TS' in subs and not 'BDMV' in subs:
                    stack.extend([os.path.join(current, each) for each in subs if each not in ['.Trashes', '.DS_Store', '.fseventsd']]) 
                    continue
            yield self._getRelativeName(current), True

    def _getRelativeName(self, path):
        ret = path[len(self.folderBase):]
        if ret and ret[0]=='/':
            ret=ret[1:]
        return ret

    def handleFile(self, folder, path):
        relPath = self._getRelativeName(folder, path)
        try:
            mInfo = mediainfo(path)
            if not mInfo:
                return #we do not handle this file /still/
        except Exception, ex:
            return #provide the exception info in ex
        name = mInfo.name or self._getTitleFromFilename(path)
        while True:
            name = raw_input("Name ["+path+' ==> '+ (name or '')+"]: ").strip() or name
            if name: 
                if name=='*':
                    print '***I***', 'discarding now this title', path
                    return
                existing = self.db.movie_find_title(name)
                if existing:
                    print '***W***', 'Already existing -this name:', path
                references = getImdbReferences(self.browser, name)
                if references:
                    break
                print '***I***','no IMDB info found for',name
        index=1
        for href, title, info in references:
            print index,'=>', title, '[', info, ']'
            index+=1
        while True:
            index = raw_input("Selection [0 to exit]: ").strip()
            if index=='0':
                return None
            index=int(index)
            if index>0 and index<=len(references):
                break
        imdbInfo= getImdbInfo(self.browser, references[index-1][0])
        if not imdbInfo.year:
            imdbInfo.year = raw_input("Year not returned by IMDB, please enter it: ").strip()
        newName = self.normalizeFilename(imdbInfo.title, path, imdbInfo.year)           
        if newName != path:
            print '***I***', 'renaming', path,'as', newName
            os.rename(path, newName)
        locationName = self._getRelativeName(folder, newName)
        self.db.storeMovie(mInfo, imdbInfo, self.location, locationName)



if __name__ == '__main__':
    for each in Location('/tmp').iterateAllFilesInPath():
        print each

