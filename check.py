import os
import re
import subprocess
import threading
import time
import sys

MAX_TIME_FMPEG_INFO = 30  # 30 seconds
MAX_TIME_MUX = 1800  # 30 minutes
FFMPEG_INFO_PATTERN = re.compile('^\s+Stream #(.+)$')
FFMPEG_INFO_SPECIFIC_PATTERN = re.compile('^(\d+):(\d+)(?:\((\w+)\))?: (Video|Audio|Subtitle):(.*)$')
LANG_BY_PRIO = ['en', 'es', 'de', 'fr', 'pt']
AUDIO_CODECS_BY_PRIO = ['ac3', 'dts', 'flac', 'vorbis', 'aac']
AUDIO_MODES_BY_PRIO = ['5.1', 'stereo', 'mono']
AUDIO_FREQUENCY_PATTERN = re.compile('^\s*(\\d\\d\\d\\d\\d) Hz\s*$')
AUDIO_RATE_PATTERN = re.compile('^\s*(\\d+) kb/s')

VIDEO_EXTENSIONS = ['.mkv']
SUBTITLE_EXTENSIONS = ['.srt']
DISMISS_EXTENSIONS = []
SUBTITLES_LANGUAGES = {'.en': 'en', '.es': 'es', '.de': 'de', '.fr': 'fr'}

CONVERT_LANGUAGES = {'eng': 'en', 'fre': 'fr', 'esp': 'es', 'ger': 'de', 'por': 'pt', 'spa': 'es'}
DISMISS_LANGUAGES = ['gre', 'chi', 'rum', 'slv', 'swe', 'hrv', 'cze', 'dut', 'fin', 'dan', 'nor', 'ice', 'ita', 'jpn', 'kor', 'cat', 'scr', 'tur', 'vie', 'bul', 'pol', 'ara']
LANGUAGES_IN_FILENAMES = {'es': 'Spanish', 'de': 'German', 'jpn': 'Japanese', 'swe': 'Sweedish', 'fr': 'French'}


_COMM_KILL = 1
_COMM_FINISHED = 2
_COMM_KILLED = 3

_DRY_RUN = False # note: is not constant
_TARGET_DIR = '.'


def _info(filename, message):
    print '#  I * [', filename, '] :', message


def _warning(filename, message):
    print '#  W  * [', filename, '] :', message


def _action_message(filename, action):
    print '# !!! * [', filename, '] :', action


def _error(filename, message):
    print
    print '  S T O P '
    print '!!!!!!! [', filename, '] :', message
    sys.exit(0)


def _process_killer(proc, max_time, communication):
    end_time = time.time() + max_time
    while communication[0] == _COMM_KILL and (time.time() < end_time) :
        time.sleep(5)
    if communication[0] == _COMM_KILL:
        proc.kill()
        communication[0] = _COMM_KILLED


def _shell(proc_args, max_time):
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


def ffmpeg_text_info(filename):
    if not os.path.isfile(filename):
        _error(filename, 'file not found')
    _, _, err = _shell("ffmpeg -i " + filename, MAX_TIME_FMPEG_INFO)
    for line in err.splitlines():
        match = FFMPEG_INFO_PATTERN.match(line)
        if match:
            yield match.group(1)


def _ffmpeg_info(filename):
    sequences = {}
    definitions = [sequences, [], [], []]
    for info in ffmpeg_text_info(filename):
        match = FFMPEG_INFO_SPECIFIC_PATTERN.match(info)
        if not match:
            _error(filename, info)
        stream, sequence, language, stream_type, more = match.groups()
        if not language:
            _error(filename, info + ' ---> missing language')
        if stream != '0':
            _error(filename, info + ' ---> missing stream ' + stream + " : expected '0'")
        seq = int(sequence)
        if language not in LANG_BY_PRIO:
            try:
                language = CONVERT_LANGUAGES[language]
            except KeyError:
                if language not in DISMISS_LANGUAGES:
                    _error(filename, 'Invalid language found:' + language)
        definitions[['Video', 'Audio', 'Subtitle'].index(stream_type) + 1].append((seq, language, more))
        sequences.append((seq, stream_type, more))
    return definitions


def _get_target_file(base):
    ret = os.path.abspath(os.path.join(_TARGET_DIR, os.path.basename(base)))
    if os.path.abspath(base) == ret:
        _error('', "Target file: " + ret + " matches original file " + base)
    return ret


def _update_dir(filename):
    if os.path.basename(filename).startswith('_') or os.path.basename(filename).startswith('_'):
        return
    video, subtitles = None, []
    for sub in os.listdir(filename):
        if not sub.startswith('.') and not sub.startswith('_'):
            fullname = os.path.join(filename, sub)
            if os.path.isdir(fullname):
                _error(filename, 'Found unexpected subdirectory ' + fullname)
            elif not fullname.startswith(filename):
                _error(filename, 'Found unexpected file ' + fullname)
            else:
                base, ext = os.path.splitext(sub.lower())
                if ext in VIDEO_EXTENSIONS:
                    if video:
                        _error(filename, 'Found multiple videos: ' + sub + "*" + video)
                    video = fullname
                elif ext in SUBTITLE_EXTENSIONS:
                    _, language = os.path.splitext(base)   # xxx.en.srt
                    try:
                        lang_extension = SUBTITLES_LANGUAGES[language]  # convert .en => eng
                    except ValueError:
                        _error(fullname, 'Incorrect subtitle language found')
                    if lang_extension in LANG_BY_PRIO:
                        subtitles.append((-_get_lang_key(lang_extension), fullname, lang_extension))
                    else:
                        _error(fullname, 'not wanted subtitle language found: ' + language)
                elif ext not in DISMISS_EXTENSIONS:
                    _error(filename, 'Found unexpected file ' + fullname)
    if not video:
        _error(filename, 'No video files found in directory')
    if not subtitles:
        _error(filename, 'No subtitles files found in directory')
    subtitles.sort()
    target = _get_target_file(video)
    command = ['mkvmerge', '-o', target, video]
    for _, name, lang in subtitles:
        command.append('--language')
        command.append('"%d:%s"' % (0, lang))
        command.append(name)
    command = ' '.join(command)
    print command
    if _DRY_RUN:
        for _, name, _ in subtitles:
            rc, out, _ = _shell('mkvmerge -i ' + name, MAX_TIME_MUX)
            if rc > 1:
                _error(name, 'SHELL: ' + out)
    else:
        rc, out, _ = _shell(command, MAX_TIME_MUX)
        if rc > 1:
            _error(command, 'SHELL: ' + out)
        else:
            print out


def _update_file(filename):
    sequences, video, audio, subtitles = _ffmpeg_info(filename)
    if len(video) != 1:
        _error(filename, "%d video streams" % len(video))
    if not audio:
        _error(filename, "%d audio streams" % len(video))
    final_videos = _sort_tracks(video, _get_video_key)
    final_audios = _sort_tracks(audio, _get_audio_key_wrapper(filename))
    final_subs = [x for x in _sort_tracks(subtitles, _get_subtitle_key) if x[1] in LANG_BY_PRIO]
    # issue warnings, if required
    if not final_subs:
        _warning(filename, 'no subtitles')
    else:
        prev = None
        for i, subs in enumerate(final_subs):
            lang = subs[1]
            if not i:
                if lang != LANG_BY_PRIO[0]:
                    _warning(filename, 'no subtitles in ' + LANG_BY_PRIO[0])
            elif prev == lang:
                _error(filename, 'multiple subtitles in ' + lang)
            prev = lang




    first_audio = final_audios[0][1]
    _check_filename_by_language(filename, first_audio)
    if final_videos[0][1] != first_audio:
        _warning(filename, 'Video language is not ' + first_audio)

    print 'Working on ', filename

    _correct_sequencing(filename, sequences, final_videos, final_audios, final_subs)

    #  if there are sequences to move, do it before modifying the defualt / forced tracks


    # final_sequences = (_correct_default_force_tracks(filename, final_videos)
    #                    + _correct_default_force_tracks(filename, final_audios)
    #                    + _correct_default_force_tracks(filename, final_subs))
    # print final_sequences
    #if final_sequences != sequences:
    # ffmpeg -i Peter_Pan__2003.mkv -f srt -i Peter_Pan__2003.en.srt -map 0:0 -map 0:1 -map 1:0 -c:v copy -c:a copy -c:s srt -metadata:s:s:0 language=eng -metadata title="Peter Pan 2003" output.mkv
    #_warning(filename, " : final sequences are " + str(final_sequences))


def _check_filename_by_language(filename, language):
    if language != LANG_BY_PRIO[0]:
        try:
            language = LANGUAGES_IN_FILENAMES[language]
        except KeyError:
            _error(filename, 'Please add ' + language + ' to variable LANGUAGES_IN_FILENAMES')
        name, ext = os.path.splitext(filename)
        if name.endswith('_' + language):
            _warning(filename, 'First language is not ' + LANG_BY_PRIO[0])
        else:
            _warning(filename, 'should end in __' + language)
            suggestion = os.path.join(os.path.dirname(filename), os.path.basename(name))+ '_' + language
            _error(filename, 'mv ' + filename + ' ' + suggestion + ext)


def update(filename):
    # audios: we support all.
    #    first one in sequence should be eng, and marked as default
    #    if no eng, use spa, else none
    # video: there should be only one, lang=first audio
    #    its language must be the same as the first audio
    # subtitles:
    #    first one in sequence should be spa and/or eng
    #    if first subtitle is not spa, mark it as default
    #    only support: spa, eng, ger, fre, por
    if os.path.isdir(filename):
        _update_dir(filename)
    else:
        _update_file(filename)


def _correct_sequencing(filename, original_sequences, videos, audios, subtitles):
    final_tracks = [x[0] for x in videos + audios + subtitles]
    if [x[0] for x in original_sequences] == final_tracks:
        return None

    print original_sequences
    for track in original_sequences:
        if track not in final_tracks:
            print track
            print videos
            print audios
            print subtitles
            break

    _error(filename, ';et me in peach')

    commands = ['ffmpeg', '-n', '-hide_banner', '-i', filename]

    for track in final_tracks:
        commands.append('-map')
        commands.append('0:%d' % track)

    commands.append('-c:v copy -c:a copy')
    if subtitles:
        commands.append('-c:s copy')

    commands.append(_get_target_file(filename))

    _error(filename, ' '.join(commands))
    # created_file = os.path.join(_TARGET_DIR, original_sequences[0][2])
    # command = ' '.join(commands + mappings + metadata + [created_file])
    # print command
    # if not _DRY_RUN:
    #     a, b, c = _shell(command, MAX_TIME_FMPEG)
    #     print a
    #     print b
    #     print c
    #
    # return created_file


def _correct_default_force_tracks(filename, tracks):
    """mkvpropedit output.mkv --edit track:4 --set flag-default=0"""

    def _action(track, forced, set):
        if _DRY_RUN:
            msg = 'remove'
            if set:
                msg = 'add'
            if forced:
                msg += ' (forced) '
            else:
                msg += ' (default) '
            _action_message(seq[2], msg + ' on track ' + str(1))
        else:
            what = 'mkvpropedit ' + filename + ' --edit track:' + str(track+1) + ' --set flag-'
            if forced:
                what = what + 'forced='
            else:
                what = what + 'default='
            if set:
                what = what + '1'
            else:
                what = what + '0'
            print what

    first = True
    for seq, _, is_default, is_forced in tracks:
        if is_forced:
            _action(seq, True, False)
        if first:
            first = False
            if not is_default:
                _action(seq, False, True)
        elif is_default:
            _action(seq, False, False)


def _sort_tracks(tracks, key_provider):
    ret, tmp = [], []
    for seq, lang, info in sorted(tracks):
        tmp.append((key_provider(lang, info), seq, lang, info))
    tmp.sort()
    for _, seq, lang, info in tmp:
        is_default = '(default)' in info
        is_forced = '(forced)' in info
        ret.append((seq, lang, is_default, is_forced))
    return ret


def _get_lang_key(lang):
    try:
        return len(LANG_BY_PRIO) - LANG_BY_PRIO.index(lang)
    except ValueError:
        return 0


def _get_subtitle_key(lang, info):
    return -_get_lang_key(lang)


def _get_video_key(lang, info):
    return _get_lang_key(lang)


def _get_audio_key_wrapper(filename):

    def _get_audio_key(lang, info):
        def _get_index(string, array, info):
            for o, c in enumerate(array):
                if c in string:
                    return str(len(array) - o)
            _warning(filename, 'unexpected ' + info + ' : ' + string)
            return '0'

        def _get_audio_frequency_key(rate):
            match = AUDIO_FREQUENCY_PATTERN.match(rate)
            if match:
                return match.group(1)
            _warning(filename, 'unexpected rate : ' + rate)
            return '00000'

        def _get_audio_rate_key(rate):
            match = AUDIO_RATE_PATTERN.match(rate)
            if match:
                ret = match.group(1)
            else:
                ret = ''
            if len(ret) > 5:
                _warning(filename, 'unexpected audio rate:' + rate)
            while len(ret) < 5:
                ret = '0' + ret
            return ret

        s = info.split(',')
        while len(s) < 5:
            s.append('*')
        return -int(''.join([str(_get_lang_key(lang)),
                            _get_index(s[0], AUDIO_CODECS_BY_PRIO, 'audio codec'),
                            _get_audio_frequency_key(s[1]),
                            _get_index(s[2], AUDIO_MODES_BY_PRIO, 'audio mode'),
                            _get_audio_rate_key(s[4])]))

    return _get_audio_key


if __name__ == '__main__':
    import argparse

    clParser = argparse.ArgumentParser(description='Movies curator')
    clParser.add_argument('-t', '--target', default='.', help='location for final files, if required')
    clParser.add_argument('-i', '--info-only', action='store_true', help='short info on the file')
    clParser.add_argument('--go', action='store_true', help='perform the required changes')
    clParser.add_argument('--only-files', action='store_true', help='only check for files')
    clParser.add_argument('--only-folders', action='store_true', help='only check for directories')
    clParser.add_argument('filenames', nargs='+')
    args = clParser.parse_args()

    if args.info_only:
        for each in args.filenames:
            print
            print each
            print '='*len(each)
            for l in ffmpeg_text_info(each):
                print l
            print
    else:
        _DRY_RUN = not args.go
        if args.target:
            if os.path.isdir(args.target):
                _TARGET_DIR = args.target
            else:
                _error(args.target, "Invalid target argument, not a directory")
        for each in args.filenames:
            if os.path.isfile(each):
                if not args.only_folders:
                    _update_file(each)
            elif os.path.isdir(each):
                if not args.only_files:
                    _update_dir(each)
            else:
                _warning(each, 'Nothing to do')
