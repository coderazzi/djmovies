import os
import re
import subprocess
import threading
import time

MAX_TIME_FMPEG_INFO = 30  # 30 seconds
MAX_TIME_FMPEG = 1800  # 30 minutes
FFMPEG_INFO_PATTERN = re.compile('^\s+Stream #(.+)$')
FFMPEG_INFO_SPECIFIC_PATTERN = re.compile('^(\d+):(\d+)(?:\((\w+)\))?: (Video|Audio|Subtitle):(.*)$')
LANG_BY_PRIO = ['eng', 'esp', 'ger', 'fre', 'por']
AUDIO_CODECS_BY_PRIO = ['ac3', 'dts', 'flac']
AUDIO_MODES_BY_PRIO = ['5.1', 'stereo', 'mono']
AUDIO_FREQUENCY_PATTERN = re.compile('^\s*(\\d\\d\\d\\d\\d) Hz\s*$')
AUDIO_RATE_PATTERN = re.compile('^\s*(\\d+) kb/s')

VIDEO_EXTENSIONS = ['.mkv']
SUBTITLE_EXTENSIONS = ['.srt']
DISMISS_EXTENSIONS = []
SUBTITLES_LANGUAGES = {'.en': 'eng'}


FFMPEG_TARGET = '/Volumes/TTC/__MOVIES'  # should be part of the arguments

_COMM_KILL = 1
_COMM_FINISHED = 2
_COMM_KILLED = 3


def _warning(filename, message):
    print '***W*** [', filename, '] :', message


def _action_message(filename, action):
    print '*  !  * [', filename, '] :', action


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
        raise Exception("Process auto-killed: " + proc_args)
    return proc.returncode, out, err


def ffmpeg_text_info(filename):
    subtitles = []
    if os.path.isdir(filename):
        video = None
        for sub in os.listdir(filename):
            if not sub.startswith('.'):
                fullname = os.path.join(filename, sub)
                if os.path.isdir(fullname):
                    raise Exception('Found unexpected subdirectory ' + fullname)
                elif not fullname.startswith(filename):
                    raise Exception('Found unexpected file ' + fullname)
                else:
                    base, ext = os.path.splitext(sub.lower())
                    if ext in VIDEO_EXTENSIONS:
                        if video:
                            raise Exception('Found multiple videos in directory ' + filename + ':' + sub + "*" + video)
                        video = fullname
                    elif ext in SUBTITLE_EXTENSIONS:
                        _, language = os.path.splitext(base)   # xxx.en.srt
                        try:
                            lang_extension = SUBTITLES_LANGUAGES[language]  # convert .en => eng
                        except ValueError:
                            raise Exception('Incorrect subtitle language found: ' + fullname)
                        if lang_extension in LANG_BY_PRIO:
                            subtitles.append(('%d:0(%s): Subtitle: external' % (len(subtitles)+1, lang_extension),
                                              fullname))
                    elif ext not in DISMISS_EXTENSIONS:
                        raise Exception('Found unexpected file: ' + fullname)
        if not video:
            raise Exception('No video files found in directory ' + filename)
        filename = video

    _, _, err = _shell("ffmpeg -i " + filename, MAX_TIME_FMPEG_INFO)
    for line in err.splitlines():
        match = FFMPEG_INFO_PATTERN.match(line)
        if match:
            yield match.group(1), 0, filename
    if subtitles:
        for i, c in enumerate(subtitles):
            yield c[0], i+1, c[1]


def _ffmpeg_info(filename):
    sequences = []
    definitions = [sequences, [], [], []]
    for info, input_stream, fullname in ffmpeg_text_info(filename):
        match = FFMPEG_INFO_SPECIFIC_PATTERN.match(info)
        if not match:
            raise Exception(filename + " : " + info)
        stream, sequence, language, stream_type, more = match.groups()
        if not language:
            raise Exception(filename + " : " + info + ' missing language')
        if int(stream) != input_stream:
            raise Exception(filename + " : " + info + ' invalid stream ' + stream + " : expected " + input_stream)
        seq = (input_stream, int(sequence), fullname)
        if seq in sequences:
            raise Exception(filename + " : multiples tracks with seq number " + str(seq))
        definitions[['Video', 'Audio', 'Subtitle'].index(stream_type) + 1].append((seq, language, more))
        sequences.append(seq)
    return definitions


def suggest(filename, do_changes):
    # audios: we support all.
    #    first one in sequence should be eng, and marked as default
    #    if no eng, use spa, else none
    # video: there should be only one, lang=first audio
    #    its language must be the same as the first audio
    # subtitles:
    #    first one in sequence should be spa and/or eng
    #    if first subtitle is not spa, mark it as default
    #    only support: spa, eng, ger, fre, por

    sequences, video, audio, subtitles = _ffmpeg_info(filename)
    if len(video) != 1:
        raise Exception(filename + " : no video streams")
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
                _warning(filename, 'multiple subtitles in ' + lang)
            prev = lang
    if not final_audios:
        _warning(filename, 'no audios')
    else:
        first_audio = final_audios[0][1]
        if first_audio != LANG_BY_PRIO[0]:
            _warning(filename, 'First language is not ' + LANG_BY_PRIO[0])
        if final_videos[0][1] != first_audio:
            _warning(filename, 'Video language is not ' + first_audio)

    _correct_sequencing(sequences, final_videos + final_audios + final_subs, do_changes)

    #  if there are sequences to move, do it before modifying the defualt / forced tracks


    # final_sequences = (_correct_default_force_tracks(filename, final_videos, do_changes)
    #                    + _correct_default_force_tracks(filename, final_audios, do_changes)
    #                    + _correct_default_force_tracks(filename, final_subs, do_changes))
    # print final_sequences
    #if final_sequences != sequences:
        # ffmpeg -i Peter_Pan__2003.mkv -f srt -i Peter_Pan__2003.en.srt -map 0:0 -map 0:1 -map 1:0 -c:v copy -c:a copy -c:s srt -metadata:s:s:0 language=eng -metadata title="Peter Pan 2003" output.mkv
        #_warning(filename, " : final sequences are " + str(final_sequences))


def _correct_sequencing(original_sequences, final_tracks, do_changes):
    if (original_sequences == [x[0] for x in final_tracks]) and (set([x[0] for x in original_sequences]) == set([0])):
        # no need to change the sequencing
        return None

    streams = set()
    commands = ['ffmpeg', '-n', '-hide_banner']
    mappings = []
    metadata = ['-c:v copy -c:a copy -c:s srt']

    for track, lang, _, _ in final_tracks:
        stream, seq, filename = track
        if stream not in streams:
            if stream:  # new subtitle
                commands.append('-f')
                commands.append('srt')
                metadata.append('-metadata:s:s:%d' % (len(streams)-1))
                metadata.append('language=%s' % lang)
            commands.append('-i')
            commands.append(filename)
            streams.add(stream)
        mappings.append('-map')
        mappings.append('%d:%d' % (stream, seq))

    created_file = os.path.join(FFMPEG_TARGET, original_sequences[0][2])
    command = ' '.join(commands + mappings + metadata + [created_file])
    print command
    if do_changes:
        a, b, c = _shell(command, MAX_TIME_FMPEG)
        print a
        print b
        print c

    return created_file


def _correct_default_force_tracks(filename, tracks, do_changes):
    """mkvpropedit output.mkv --edit track:4 --set flag-default=0"""

    def _action(track, forced, set):
        if do_changes:
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
        else:
            msg = 'remove'
            if set:
                msg = 'add'
            if forced:
                msg += ' (forced) '
            else:
                msg += ' (default) '
            _action_message(seq[2], msg + ' on track ' + str(1))

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
    pass


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


def help():
    print '[-i] files : information about the files, as provided by ffmpeg -i'
    print '[-s] files : suggest changes into the files'
    print '[-ss] files : suggest changes into the files, and perform basic actions'


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        help()
    elif sys.argv[1] == '-i':
        for each in sys.argv[2:]:
            print '\n', each
            print '='*len(each)
            for l in ffmpeg_text_info(each):
                print l[0]
    elif sys.argv[1] == '-s':
        for each in sys.argv[2:]:
            suggest(each, False)
    elif sys.argv[1] == '-ss':
        for each in sys.argv[2:]:
            suggest(each, True)
