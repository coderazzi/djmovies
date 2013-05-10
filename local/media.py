#See http://paltman.github.com/pymediainfo
#[this file is https://github.com/paltman/pymediainfo/blob/master/pymediainfo/__init__.py]

import os, re, subprocess, sys

from xml.dom import minidom
from xml.parsers.expat import ExpatError
from tempfile import mkstemp

from dstruct import Struct
from locations import LocationHandler

_py3 = sys.version_info >= (3,)

# check if system has simplejson installed, otherwise
# fall back to json (included in stdlib in 2.6+)
try:
    import simplejson as json
except ImportError:
    import json

# __version__ = '1.3.2'

ENV_DICT = {
    "PATH": "/usr/local/bin/:/usr/bin/",
    "LD_LIBRARY_PATH": "/usr/local/lib/:/usr/lib/"}


class Track(object):

    def __getattribute__(self, name):
        try:
            return object.__getattribute__(self, name)
        except:
            pass
        return None

    def __init__(self, xml_dom_fragment):
        self.xml_dom_fragment = xml_dom_fragment
        self.track_type = self.xml_dom_fragment.attributes['type'].value
        for el in self.xml_dom_fragment.childNodes:
            if el.nodeType == 1:
                node_name = el.nodeName.lower().strip().strip('_')
                if node_name == 'id':
                    node_name = 'track_id'
                node_value = el.firstChild.nodeValue
                other_node_name = "other_%s" % node_name
                if getattr(self, node_name) is None:
                    setattr(self, node_name, node_value)
                else:
                    if getattr(self, other_node_name) is None:
                        setattr(self, other_node_name, [node_value, ])
                    else:
                        getattr(self, other_node_name).append(node_value)

        for o in [d for d in self.__dict__.keys() if d.startswith('other_')]:
            try:
                primary = o.replace('other_', '')
                setattr(self, primary, int(getattr(self, primary)))
            except:
                for v in getattr(self, o):
                    try:
                        current = getattr(self, primary)
                        setattr(self, primary, int(v))
                        getattr(self, o).append(current)
                        break
                    except:
                        pass

    def __repr__(self):
        return("<Track track_id='{0}', track_type='{1}'>".format(self.track_id, self.track_type))

    def to_data(self):
        data = {}
        for k, v in self.__dict__.iteritems():
            if k != 'xml_dom_fragment':
                data[k] = v
        return data


class MediaInfo(object):

    def __init__(self, xml):
        self.xml_dom = xml
        if _py3: xml_types = (str,)     # no unicode type in python3
        else: xml_types = (str, unicode)

        if isinstance(xml, xml_types):
            self.xml_dom = MediaInfo.parse_xml_data_into_dom(xml)

    @staticmethod
    def parse_xml_data_into_dom(xml_data):
        dom = None
        try:
            dom = minidom.parseString(xml_data)
        except ExpatError:
            try:
                dom = minidom.parseString(xml_data.replace("<>00:00:00:00</>", ""))
            except:
                pass
        except:
            pass
        return dom

    @staticmethod
    def parse(filename, environment=ENV_DICT):
        command = ["mediainfo", "-f", "--Output=XML", filename]
        fileno_out, fname_out = mkstemp(suffix=".xml", prefix="media-")
        fileno_err, fname_err = mkstemp(suffix=".err", prefix="media-")
        fp_out = os.fdopen(fileno_out, 'r+b')
        fp_err = os.fdopen(fileno_err, 'r+b')
        p = subprocess.Popen(command, stdout=fp_out, stderr=fp_err, env=environment)
        p.wait()
        fp_out.seek(0)

        xml_dom = MediaInfo.parse_xml_data_into_dom(fp_out.read())
        fp_out.close()
        fp_err.close()
        return MediaInfo(xml_dom)

    def _populate_tracks(self):
        if self.xml_dom is None:
            return
        for xml_track in self.xml_dom.getElementsByTagName("track"):
            self._tracks.append(Track(xml_track))

    @property
    def tracks(self):
        if not hasattr(self, "_tracks"):
            self._tracks = []
        if len(self._tracks) == 0:
            self._populate_tracks()
        return self._tracks

    def to_data(self):
        data = {'tracks': []}
        for track in self.tracks:
            data['tracks'].append(track.to_data())
        return data

    def to_json(self):
        return json.dumps(self.to_data())

def runProcess(exe):    
    p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      if line:
        yield line
      if(retcode is not None):
        break

def mediainfo(path, folder):
    def mount(isoFile):   
        disk, path, first=None, None, True
        for line in runProcess(['hdiutil', 'mount', isoFile]):
            if first:
                first=False         
                match = re.match('^(/dev/d\S+)\s*(/.*)$', line)
                if match:
                    disk, path = match.group(1), match.group(2)
        return path

    def umount(diskOrPath):
        for line in runProcess(['hdiutil', 'eject', diskOrPath]):
            if 'failed' in line:
                print '***E***', line

    def get_subs(path):
        dirs, files=[], []
        stack=[path]
        while stack:
            use=stack.pop()
            dirs.append(os.path.basename(use))
            for each in os.listdir(use):
                p=os.path.join(use, each)
                if os.path.isdir(p):
                    stack.append(p)
                else:
                    files.append(p)
        return dirs, files

    def retSize(size):
        return 0.01*round(size/(1024*1024*10.24)) 

    def getTitleFromFilename(filename):
        use=re.sub('\([^)]*\)', '', re.sub('_+', ' ', os.path.splitext(os.path.basename(filename))[0])).strip()
        use = re.sub('(\\S)([A-Z])(\\S)','\\1 \\2\\3', use)
        use = re.sub('(.*)\s+\d\d\d\d','\\1', use).strip()
        return use

    def invoke_mi(paths):
        name, width, height, audios, texts = None, None, None, set(), set()
        size, wsize, duration = 0, 0, 0.0

        for path in paths:
            size+=os.path.getsize(path)
            for track in MediaInfo.parse(path).tracks:
                if track.track_type=='General':
                    name = name or track.name
                    duration += float(track.duration or 0)
                elif track.track_type=='Video':
                    w, h = track.width, track.height
                    if w and h and (w*h>wsize):
                        width, height, wsize = w, h, w*h
                elif track.track_type=='Audio':
                    now = track.other_language
                    if now:
                        now = now[0]
                    else:
                        now='?'
                    audios.add(now)
                elif track.track_type=='Text':
                    now = track.other_language
                    if now:
                        now = now[0]
                    else:
                        now='?'
                    texts.add(now) 

        duration = int(round(duration/60000)) if duration else None
        size = retSize(size)
        return Struct.nonulls(name=name, size=size, duration=duration, width=width, height=height, 
            audios='/'.join(audios), texts='/'.join(texts))


    def process(path, folder):
        path=os.path.join(folder, path)
        extension=os.path.splitext(path)[-1].lower()
        if extension:
            extension=extension[1:].title()
        type = LocationHandler(folder).getType(path)
        if type in [LocationHandler.VIDEO_FILE, LocationHandler.VIDEO_FILE_ALONE_IN_DIR]:
            ret= invoke_mi([path])
            ret.format=extension
            return ret
        if type in [LocationHandler.IMAGE_FILE, LocationHandler.IMAGE_FILE_ALONE_IN_DIR]:
            mpath=mount(path)
            if not mpath:
                raise Exception("Could not mount:"+path)
            try:
                ret = mediainfo(os.path.basename(mpath), os.path.dirname(mpath))
                if ret:
                    if ret.format=='BlueRay':
                        ret.format+=' '+extension
                    else:
                        ret.format = extension
                return ret
            finally:
                umount(mpath)
        if type in [LocationHandler.DVD_FOLDER, LocationHandler.DVD_FOLDER_DIRECT, LocationHandler.BLUE_RAY_FOLDER]:
            dirs, files = get_subs(path)
            if type==LocationHandler.BLUE_RAY_FOLDER:
                files=[f for f in files if f.lower().endswith('.m2ts')]
                if files:
                    mi = invoke_mi(files)
                    mi.format='BlueRay'
                    return mi
            else:
                mi = invoke_mi([path])
                mi.format='DVD'
                size=0
                for each in files:
                    size+=os.path.getsize(each)
                mi.size=retSize(size)
                return mi
        return None

    ret=process(path, folder)
    if ret and not ret.name:
        ret.name = getTitleFromFilename(path)
    return ret



    
if __name__ == '__main__':
    # movie='/Volumes/Movies_III/How_The_West_Was_Won__1962.iso'
    folder='/Volumes/Movies_V/'
    movie='American_Gangster__2007.mkv'
    info= mediainfo(movie, folder)
    for i in dir(info):
        print i, getattr(info, i)
