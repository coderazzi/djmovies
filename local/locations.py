import re
import os

class LocationHandler:

    VIDEO_FILE='VIDEO_FILE'
    VIDEO_FILE_ALONE_IN_DIR='VIDEO_FILE_ALONE_IN_DIR'
    IMAGE_FILE='IMAGE_FILE'
    IMAGE_FILE_ALONE_IN_DIR='IMAGE_FILE_ALONE_IN_DIR'
    DVD_FOLDER='DVD_FOLDER'
    DVD_FOLDER_DIRECT='DVD_FOLDER_DIRECT'
    BLUE_RAY_FOLDER='BLUE_RAY_FOLDER'
    UNVISITED_FOLDER='UNVISITED_FOLDER'
    UNHANDLED_FILE='UNHANDLED_FILE'

    VIDEO_EXTENSIONS=['avi', 'mkv', 'mp4', 'divx', 'vob', 'm2ts', 'wmv', 'ts']
    IMAGE_EXTENSIONS=['iso', 'img']
    EXT_VIDEO_EXTENSIONS=VIDEO_EXTENSIONS+IMAGE_EXTENSIONS+['ifo', 'bup']
    SUBTITLE_EXTENSIONS=['srt', 'sub', 'idx']

    def __init__(self, folderBase):
        self.folderBase=folderBase

    def isValid(self):
        return os.path.isdir(self.folderBase)

    def getType(self, filename):
        '''
        Returns the type of a file PROPERLY handled in a previous iteration, that is, not belonging
        to UNVISITED_FOLDER / UNHANDLED_FILE
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
            if extension in LocationHandler.IMAGE_EXTENSIONS:
                if os.path.dirname(filename):
                    return LocationHandler.IMAGE_FILE_ALONE_IN_DIR        
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
            C-IMAGE_FILE: a ISO or IMG file, on top folder
            D-IMAGE_FILE_ALONE_IN_DIR: a ISO or IMG file, alone in top subfolder
            E-DVD_FOLDER: a top folder that contains, optionally, a AUDIO_TS folder, and, definitely,
                a VIDEO_TS folder, containing BUP & IFO & VOB files. Any additional files or folder is
                reported separately
            F-DVD_FOLDER_DIRECT: a top folder containing nosubdirs and files of type BUP & IFO & VOB. 
            G-BLUE_RAY_FOLDER: a top folder containing a BDMV folder
            H-UNVISITED_FOLDER: any folder not treated above (or error)
            I-UNHANDLED_FILE: any file not treated above (or error)
        4- In case of  VIDEO_FILE_ALONE_IN_DIR or IMAGE_FILE_ALONE_IN_DIR or DVD_FOLDER, a list
            of subtitle files
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
                        if extension in LocationHandler.IMAGE_EXTENSIONS:
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
                            if extension in LocationHandler.SUBTITLE_EXTENSIONS:
                                ok_files.append(fullname)
                                continue
                        other_files.append(fullname)
                    if subdirs:                        
                        if 'VIDEO_TS' in subdirs:
                            other_files+=video_files.keys()
                            ret.append((filename, False, LocationHandler.DVD_FOLDER, [os.path.basename(each) for each in ok_files]))
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
                            unique, extension = video_files.popitem()
                            if extension in LocationHandler.IMAGE_EXTENSIONS:
                                assoc = LocationHandler.IMAGE_FILE_ALONE_IN_DIR
                            elif extension in LocationHandler.VIDEO_EXTENSIONS:
                                assoc=LocationHandler.VIDEO_FILE_ALONE_IN_DIR
                            else:
                                assoc=None
                                other_files.append(unique)
                            if assoc:
                                ret.append((unique, False, assoc, [os.path.basename(each) for each in ok_files]))
                        else:
                            if False in [each in ['vob', 'ifo', 'bup'] for each in video_files.values()]:
                                other_files+=ok_files+video_files.keys()
                            else:
                                ret.append((filename, False, LocationHandler.DVD_FOLDER_DIRECT))
                                other_files.extend(ok_files)
                    else:
                        other_files.extend(ok_files)
                    for each in other_files:
                        ret.append((each, False, LocationHandler.UNHANDLED_FILE))
            except OSError:
                ret.append((filename, True, LocationHandler.UNHANDLED_FILE)) #even for dirs, it is okay
        return ret


    def normalizeFilename(self, path, imdbInfo):
        
        title, year = imdbInfo.title, imdbInfo.year
        if not title:
            return path

        newname=re.sub('[^a-z0-9]+', '_', title.lower()).title() + ((year and ('__'+year)) or '')
        oldDirName=None

        dirname, basename=os.path.dirname(path), os.path.basename(path)
        if dirname and dirname!=newname:
            #we rename it
            oldDirName = os.path.join(self.folderBase, dirname)
            newDirName = os.path.join(self.folderBase, newname)
            os.rename(oldDirName, newDirName)
            dirname=newname
        newname+=os.path.splitext(basename)[-1].lower()
        if newname!=basename:
            oldPath = os.path.join(self.folderBase, dirname, basename)
            newPath = os.path.join(self.folderBase, dirname, newname)
            basename = newname
            try:
                #if this fails, we will rename the directory back
                os.rename(oldPath, newPath)
            except:
                if oldDirName:
                    os.rename(newDirName, oldDirName)
                raise
        return os.path.join(dirname, basename)

    def reverseNormalization(self, path, normalizedName):
        oldDirname, normDirname = os.path.dirname(path), os.path.dirname(normalizedName)
        oldName, normName = os.path.basename(path), os.path.basename(normalizedName)

        if oldDirname!=normDirname:
            os.rename(os.path.join(self.folderBase, normDirname), os.path.join(self.folderBase, oldDirname))

        if oldName!=normName:
            os.rename(os.path.join(self.folderBase, oldDirname, normName), os.path.join(self.folderBase, oldDirname, oldName))

    def getRelativeName(self, path):
        ret = path[len(self.folderBase):]
        if ret and ret[0]=='/':
            ret=ret[1:]
        return ret




# if __name__ == '__main__':
#     from dstruct import Struct
#     import time
#     lc = LocationHandler('/tmp')
#     name='kk/kk.mkv'
#     newname=lc.normalizeFilename(name, Struct(year='1992', title='EL pajaro'))
#     print newname
#     time.sleep(5)
#     lc.reverseNormalization(name, newname)
#     print 'Done'



