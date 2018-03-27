import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time


_DRY_RUN = False  # note: is not constant
_TARGET_DIR = None

VIDEO_EXTENSIONS = set(['.mkv', '.avi', '.mp4', '.mov', '.wmv' , '.mpg', '.rmvb', '.divx', '.m4v', '.flv', '.mpeg', '.iso'])
IMAGE_EXTENSIONS = set(['.jpg', '.png', '.gif', '.jpeg'])
DISMISS_EXTENSIONS = set(['.srt', '.nfo', '.db', '.sfv', '.srr', '.html', '.md5', '.doc', '.txt', '.htm'])

IGNORE_FOLDER = '.69-ok'

MAX_VIDEOS_TO_MERGE = 12
MAX_IMAGES_TO_DISMISS = 12

_COMM_KILL = 1
_COMM_FINISHED = 2
_COMM_KILLED = 3
MAX_TIME_CONCAT=3600 #60 minutes

CONCAT_PATTERN = re.compile('^Concat Output Path: (.*)$')

class Exit(Exception):
    pass


def _show(func, filename, message):
    func('%s\t\t%s', filename, message)


def _info(filename, message):
    if message:
        _show(logging.info, filename, message)


def _warning(filename, message):
    _show(logging.warning, filename, message)


def _error(filename, message):
    _show(logging.error, filename, message)
    raise Exit


def _shell(proc_args, max_time):
    def _process_killer(proc, max_time, communication):
        end_time = time.time() + max_time
        while communication[0] == _COMM_KILL and (time.time() < end_time) :
            time.sleep(5)
        if communication[0] == _COMM_KILL:
            proc.kill()
            communication[0] = _COMM_KILLED

    proc = subprocess.Popen(proc_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    thread_communication = [True]
    thread = threading.Thread(target=_process_killer, args=(proc, max_time, thread_communication))
    thread.setDaemon(True)
    thread.start()
    out, err = proc.communicate()
    killed = thread_communication[0] == _COMM_KILLED
    thread_communication[0] = _COMM_FINISHED
    if killed:
        _error("Process auto-killed", proc_args)
    return proc.returncode, out, err


def _exec_concat(path, videos, arg_name=None):
    command = os.path.join(os.path.dirname(__file__) or '.', 'concat.sh')
    if arg_name:
        command += " -a"+arg_name
    for v in sorted(videos):
        command = command + ' "%s"' % v
    _info(path, command)
    rc, out, err = _shell(command, MAX_TIME_CONCAT)
    if rc > 1:
        _error(path, 'SHELL: ' + out)
        return False
    match = CONCAT_PATTERN.match(out.splitlines()[-1])
    if not match:
        _error(path, 'SHELL: ' + err)
        return False
    if not os.path.exists(match.group(1)):
        _error(path, 'concat.sh, missing ' + match.group(1))
        return False
    return True


def _process_video(path, videos, extension):
    if len(videos) == 1:
        # just move it up, putting to it the name of the folder (add the extension)
        os.rename(videos[0], path+extension)
    else:
        if not _exec_concat(path, videos):
            return False
    try:
        shutil.rmtree(path)
    except OSError:
        _error(path, "Cannot remove?")
        raise
    return True


def _group(filenames):
    stack = [f for f in filenames if os.path.isdir(f)]
    if len(stack) != 1:
        _error('group', 'must be used on exactly one folder')
        return

    for base, group in _get_folder_videos(stack[0]):
        if len(group) > 1:
            argname = re.sub('_+', '_', re.sub('\W', '_', base))
            if _DRY_RUN:
                for each in group:
                    _info(argname, each)
            else:
                _exec_concat(base, group, argname)


def _get_folder_videos(folder):
    pattern = re.compile("(.*?)\d+$")
    videos = {}  # mapped by extension
    for each in os.listdir(folder):
        if not each.startswith('.'):
            path = os.path.join(folder, each)
            if os.path.isfile(path):
                base, ext = os.path.splitext(each)
                match = pattern.match(base)
                if match:
                    base = match.group(1)
                ext = ext.lower()
                if ext in VIDEO_EXTENSIONS:
                    try:
                        sub_videos = videos[ext]
                    except KeyError:
                        sub_videos = videos[ext] = {}
                    try:
                        group = sub_videos[base]
                    except KeyError:
                        group = sub_videos[base] = []
                    group.append(path)
    for each in videos.values():
        for base, group in each.items():
            yield base, sorted(group)


def _process(filenames, force):
    stack = [f for f in filenames if os.path.isdir(f)]
    if force and len(stack) > 1:
        _error('force', 'used on more than one folder')
        return
    unknown_extensions = set()
    while stack:
        folder = stack.pop(0)
        subfolders, videos, images, others, ignore, video_extension = _get_folder_info(folder)
        if ignore:
            _info(folder, "Folder ignored")
        elif others:
            unknown_extensions = unknown_extensions.union(others)
        elif subfolders:
            stack = stack + subfolders
            if force:
                _error('force', 'Can only be used on a final folder')
                return
        else:
            vlen, ilen = len(videos), len(images)
            if vlen:
                if not video_extension:
                    _warning(folder, "Videos of different formats")
                elif vlen > MAX_VIDEOS_TO_MERGE and not force:
                    _warning(folder, "Too many videos")
                elif ilen > MAX_IMAGES_TO_DISMISS and not force:
                    _warning(folder, "Too many images to dismiss")
                else:
                    _info(folder, "Process VIDEO")
                    if not _DRY_RUN:
                        if not _process_video(folder, videos, video_extension):
                            return
            elif ilen:
                _info(folder, "IMAGES folder")
            else:
                _warning(folder, "Remove empty directory")
    if unknown_extensions:
        _warning('*', "Unknown extensions : " + str(unknown_extensions))


def _get_folder_info(folder):
    subfolders, videos, images, others, ignore, video_extension = [], [], [], set(), False, None
    for each in os.listdir(folder):
        if each .startswith('.'):
            if each == IGNORE_FOLDER:
                ignore = True
        else:
            path = os.path.join(folder, each)
            if os.path.isdir(path):
                subfolders.append(path)
            else:
                ext = os.path.splitext(each)[1].lower()
                if ext in VIDEO_EXTENSIONS:
                    if videos:
                        if ext != video_extension:
                            video_extension=None
                    else:
                        video_extension = ext
                    videos.append(path)
                elif ext in IMAGE_EXTENSIONS:
                    images.append(path)
                elif ext not in DISMISS_EXTENSIONS:
                    others.add(ext)
                    _warning(path, "unexpected file extension")
    return sorted(subfolders), videos, images, others, ignore, video_extension


def main(parser, sysargs):
    global _DRY_RUN, _TARGET_DIR

    args = parser.parse_args(sysargs)

    _DRY_RUN = not args.go
    if args.go:
        logging.basicConfig(filename=os.path.join(os.path.dirname(__file__), 'normalize.log'),
                            format='%(asctime)s\t  %(levelname)-8s %(message)s',
                            level=logging.INFO)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s\t  %(levelname)-8s %(message)s', datefmt='%I:%M:%S')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
    else:
        logging.basicConfig(format='%(levelname)-8s %(message)s',
                            level=logging.INFO)

    if args.target:
        if os.path.isdir(args.target):
            _TARGET_DIR = args.target
        else:
            _error(args.target, "Invalid target argument, not a directory")
    try:
        if args.group:
            _group(args.filenames)
        else:
            _process(args.filenames, args.force and not _DRY_RUN)  # only allow force with --go
    except Exit:
        if not _DRY_RUN:
            sys.exit(0)


if __name__ == '__main__':
    import argparse

    clParser = argparse.ArgumentParser(description='Movies curator')
    clParser.add_argument('-t', '--target', help='location for final files, if required')
    clParser.add_argument('--force', action='store_true', help='forces the processing of video on a given folder')
    clParser.add_argument('--group', action='store_true', help='groups videos in a folder by name')
    clParser.add_argument('--go', action='store_true', help='perform the required changes')
    clParser.add_argument('filenames', nargs='+')

    if sys.stdin.isatty():
        # not run as tty
        main(clParser, sys.argv[1:])
    else:
        for f in sys.stdin.readlines():
            i = f.strip()
            if i:
                main(clParser, sys.argv[1:] + [i])
