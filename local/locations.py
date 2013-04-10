import re
import os

class LocationHandler:

    VIDEO_FILE='VIDEO_FILE'
    VIDEO_FILE_ALONE_IN_DIR='VIDEO_FILE_ALONE_IN_DIR'
    ADDITIONAL_FILE_IN_DIR='ADDITIONAL_FILE_IN_DIR'
    IMAGE_FILE='IMAGE_FILE'
    DVD_FOLDER='DVD_FOLDER'
    DVD_FOLDER_DIRECT='DVD_FOLDER_DIRECT'
    BLUE_RAY_FOLDER='BLUE_RAY_FOLDER'
    UNVISITED_FOLDER='UNVISITED_FOLDER'
    UNHANDLED_FILE='UNHANDLED_FILE'

    VIDEO_EXTENSIONS=['avi', 'mkv', 'mp4', 'divx', 'vob', 'm2ts', 'wmv', 'ts']
    EXT_VIDEO_EXTENSIONS=VIDEO_EXTENSIONS+['ifo', 'bup']
    OK_EXTENSIONS=['srt', 'sub', 'idx']

    def __init__(self, folderBase):
        self.folderBase=folderBase

    def isValid(self):
        return os.path.isdir(self.folderBase)

    def getType(self, filename):
        '''
        Returns the type of a file PROPERLY handled in a previous iteration, that is, not belonging
        to ADDITIONAL_FILE_IN_DIR / UNVISITED_FOLDER / UNHANDLED_FILE
        '''
        fullname = os.path.join(self.folderBase, filename)
        if os.path.isdir(fullname):
            subdirs=[each for each in os.listdir(fullname) if os.path.isdir(os.path.join(fullname, each))]
            if 'VIDEO_TS' in subdirs:
                return LocationHandler.DVD_FOLDER
            if 'BDMV' in subdirs:
                return LocationHandler.BLUE_RAY_FOLDER
            return LocationHandler.DVD_FOLDER_DIRECT
        extension=os.path.splitext(filename)[-1].lower()
        if extension:
            extension = extension[1:].lower() 
            if extension in ['iso', 'img']:
                return LocationHandler.IMAGE_FILE
            if extension in LocationHandler.VIDEO_EXTENSIONS:
                if os.path.dirname(filename):
                    return LocationHandler.VIDEO_FILE_ALONE_IN_DIR        
                return LocationHandler.VIDEO_FILE
        return LocationHandler.UNHANDLED_FILE


    def iterateAllFilesInPath(self):
        '''
        Iterates over the folder base, returning information on the files found.
        The iteration is essentially not recursive, although it indeed searches into subdirectories
          as far as some rules are applied.
        It returns a list of tuples containing:
        1- Name of the file or folder, relative to the folder base. A folder is itself only returned
           when it has a meaning on itself (it contains a VIDEO_TS folder or BDMV folder), or when it
           is being discarded (see 3rd element in the tuple), or to report an error.
        2- Error flag: if this flag is set, this file / folder couldn't be read
        3- type of file:
            A-VIDEO_FILE: a file with a proper video extension, not contained in any folder
            B-VIDEO_FILE_ALONE_IN_DIR: like A, but found in a top level folder (that is, not in folder
                inside a folder). This folder cannot contain any subdirectory or other VIDEO files.
            C-ADDITIONAL_FILE_IN_DIR: a file in the same folder as a VIDEO_FILE_ALONE_IN_DIR file,
                and with a valid extension (srt, sub, idx)
            D-IMAGE_FILE: a ISO or IMG file, on top folder
            E-DVD_FOLDER: a top folder that contains, optionally, a AUDIO_TS folder, and, definitely,
                a VIDEO_TS folder, containing BUP & IFO & VOB files. Any additional files or folder is
                reported separately
            F-DVD_FOLDER_DIRECT: a top folder containing nosubdirs and files of type BUP & IFO & VOB. 
            G-BLUE_RAY_FOLDER: a top folder containing a BDMV folder
            H-UNVISITED_FOLDER: any folder not treated above (or error)
            I-UNHANDLED_FILE: any file not treated above (or error)
        '''
        files=None
        try: 
            if os.path.isdir(self.folderBase): 
                files=os.listdir(self.folderBase)
        except OSError: pass
        if files==None: return [(self.folderBase, True, LocationHandler.UNVISITED_FOLDER)]

        ret=[]
        for filename in files:
            if filename[0]=='.': continue
            full=os.path.join(self.folderBase, filename)
            try:
                if not os.path.isdir(full):
                    #simple case: top path, or file is video_file, or iso/img, or just handled
                    extension=os.path.splitext(full)[-1].lower()
                    type=LocationHandler.UNHANDLED_FILE
                    if extension:
                        extension=extension[1:].lower()
                        if extension in ['iso', 'img']:
                            type=LocationHandler.IMAGE_FILE
                        elif extension in LocationHandler.VIDEO_EXTENSIONS:
                            type=LocationHandler.VIDEO_FILE
                    ret.append((filename, False, type))
                else:
                    #complicated case: a subdir with content, let's classify what is inside
                    #we do not recurse now to more subdir levels
                    subdirs, video_files, ok_files, other_files={}, {}, [], []
                    for each in os.listdir(full):
                        if each[0]=='.': continue
                        absname = os.path.join(full, each)
                        fullname=self.getRelativeName(absname)
                        try:
                            if os.path.isdir(absname):
                                subdirs[each]=fullname
                                continue
                        except OSError:
                            ret.append((fullname, True, LocationHandler.UNHANDLED_FILE))
                            continue
                        extension=os.path.splitext(each)[-1].lower()
                        if extension:
                            extension=extension[1:].lower()
                            if extension in LocationHandler.EXT_VIDEO_EXTENSIONS:
                                video_files[fullname]=extension
                                continue
                            if extension in LocationHandler.OK_EXTENSIONS:
                                ok_files.append(fullname)
                                continue
                        other_files.append(fullname)
                    if subdirs:                        
                        if 'VIDEO_TS' in subdirs:
                            ret.append((filename, False, LocationHandler.DVD_FOLDER))
                            other_files+=ok_files+video_files.keys()
                            ok_files=video_files=[]
                            subdirs.pop('VIDEO_TS')
                            try: subdirs.pop('AUDIO_TS')
                            except: pass
                        elif 'BDMV' in subdirs:
                            ret.append((filename, False, LocationHandler.BLUE_RAY_FOLDER))
                            subdirs.pop('BDMV')
                            other_files+=ok_files+video_files.keys()
                            ok_files=video_files=[]
                        for each in subdirs.values():
                            ret.append((each, False, LocationHandler.UNVISITED_FOLDER))
                    if video_files:
                        if len(video_files)==1:
                            ret.append((video_files.popitem()[0], False, LocationHandler.VIDEO_FILE_ALONE_IN_DIR))
                            for each in ok_files:
                                ret.append((each, False, LocationHandler.ADDITIONAL_FILE_IN_DIR))
                        else:
                            if False in [each in ['vob', 'ifo', 'bup'] for each in video_files.values()]:
                                other_files+=ok_files+video_files.keys()
                            else:
                                ret.append((full, False, LocationHandler.DVD_FOLDER_DIRECT))
                                other_files.extend(ok_files)
                    else:
                        other_files.extend(ok_files)
                    for each in other_files:
                        ret.append((each, False, LocationHandler.UNHANDLED_FILE))
            except OSError:
                ret.append((filename, True, LocationHandler.UNHANDLED_FILE)) #even for dirs, it is okay
        return ret


    def DEPR_iterateAllFilesInPath(self):
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
            yield self.getRelativeName(current), True

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
        return self.getRelativeName(newName)

    def reverseNormalization(self, path, normalizedName):
        fullpath = os.path.join(self.folderBase, path)
        fullNormalizedPath = os.path.join(self.folderBase, normalizedName)
        if fullNormalizedPath!=fullPath:
            os.rename(fullNormalizedPath, fullpath)

    def getRelativeName(self, path):
        ret = path[len(self.folderBase):]
        if ret and ret[0]=='/':
            ret=ret[1:]
        return ret




if __name__ == '__main__':
    for each in LocationHandler('/tmp').newIterateAllFilesInPath():
        print each

