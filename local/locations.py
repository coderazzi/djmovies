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

    def normalizeFilename(self, path, imdbInfo):
        def _normalizeFilename(filename, title, year):
            if not title: return filename
            year = (year and ('__'+year)) or ''
            basename=re.sub('[^a-z0-9]+', '_', title.lower()).title()
            return os.path.join(os.path.dirname(filename), basename+year+os.path.splitext(filename)[-1].lower())
        fullpath = os.path.join(self.folderBase, path)
        newName = _normalizeFilename(fullpath, imdbInfo.title, imdbInfo.year)
        if newName != fullpath:
            os.rename(fullpath, newName)
        return self._getRelativeName(newName)

    def reverseNormalization(self, path, normalizedName):
        fullpath = os.path.join(self.folderBase, path)
        fullNormalizedPath = os.path.join(self.folderBase, normalizedName)
        if fullNormalizedPath!=fullPath:
            os.rename(fullNormalizedPath, fullpath)

    def _getRelativeName(self, path):
        ret = path[len(self.folderBase):]
        if ret and ret[0]=='/':
            ret=ret[1:]
        return ret




if __name__ == '__main__':
    for each in LocationHandler('/tmp').iterateAllFilesInPath():
        print each

