import os
import re
import subprocess
import threading
import time


# --go required always to do changes
# --just-corrections changes handle by mkvpropedit, things like changing a track name, default / forced. etc
# --only-check-audios ensures that only audios are handled

# imagine only one call -probably not good-
# case:
#   one audio EN: ok
#   several audios EN:
#       only one not marked as commentary: OK
#       one or more audios not marked as commentary:
#           check title:
#               if all have title === English (AC3), etc: good, sort by current system
#               else:


# Audios: normalized MEANS Emglish (AC3) - commentary XX
# If there is only one English: English - commentary XX


MAX_TIME_FMPEG_INFO = 30  # 30 seconds
MAX_TIME_MUX = 3600  # 60 minutes
FFMPEG_INFO_PATTERN = re.compile('^\s+Stream #(.+)$')
FFMPEG_STREAM_TITLE_PATTERN = re.compile('^\s+title\s+:\s+(.+)$')
FFMPEG_TITLE_PATTERN = re.compile('^    title\s+:\s+(.+)$')
FFMPEG_INFO_SPECIFIC_PATTERN = re.compile('^(\d+):(\d+)(?:\((\w+)\))?: (Video|Audio|Subtitle):(.*)$')
LANG_BY_PRIO = ['en', 'es', 'de', 'fr', 'pt']
AUDIO_CODECS_BY_PRIO = ['ac3', 'dts', 'flac', 'vorbis', 'aac']
AUDIO_MODES = ['5.1', 'stereo', 'mono', '6.1', '7.1']
AUDIO_FREQUENCY_PATTERN = re.compile('^\s*(\\d\\d\\d\\d\\d) Hz\s*$')
AUDIO_RATE_PATTERN = re.compile('^\s*(\\d+) kb/s')
FILENAME_PATTERN = re.compile('(.*?)__(\d\d\d\d)(?:_\w+)?(?:_\w+)?\.\w+$')

VIDEO_EXTENSIONS = ['.mkv']
SUBTITLE_EXTENSIONS = ['.srt']
DISMISS_EXTENSIONS = []
SUBTITLES_LANGUAGES = {'.en': 'en', '.es': 'es', '.de': 'de', '.fr': 'fr'}

CONVERT_LANGUAGES = {'eng': 'en', 'fre': 'fr', 'esp': 'es', 'ger': 'de', 'por': 'pt', 'spa': 'es'}
DISMISS_LANGUAGES = ['gre', 'chi', 'rum', 'slv', 'swe', 'hrv', 'cze', 'dut', 'fin', 'dan', 'nor', 'ice', 'ita', 'jpn', 'kor', 'cat', 'scr', 'tur', 'vie', 'bul', 'pol', 'ara']
LANGUAGES = {'es': 'Spanish', 'de': 'German', 'jpn': 'Japanese', 'swe': 'Swedish', 'fr': 'French', 'en': 'English'}


_COMM_KILL = 1
_COMM_FINISHED = 2
_COMM_KILLED = 3

_DRY_RUN = False # note: is not constant
_TARGET_DIR = '.'


def _info(filename, message):
    print '#  I  * [', filename, '] :', message


def _warning(filename, message):
    print '#  W  * [', filename, '] :', message


def _action_message(filename, action):
    print '# !!! * [', filename, '] :', action


def _error(filename, message):
    print
    print '  S T O P '
    print '!!!!!!! [', filename, '] :', message
    print
    raise message


def _mkvmerge_launch(command, name_if_error):
    rc, out, _ = _shell(command, MAX_TIME_MUX)
    if rc > 1:
        _error(name_if_error, 'SHELL: ' + out)
    return out


def _mkvpropedit_launch(command, name_if_error):
    rc, out, _ = _shell(command, MAX_TIME_MUX)
    if rc:
        _error(name_if_error, 'SHELL: ' + out)


def _ffmpeg_launch(command):
    rc, out, err = _shell(command, MAX_TIME_MUX)
    if rc > 0:
        print rc
        _error('ffmpeg', err)
    return err


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
    title, ret = None, []
    for line in _ffmpeg_launch("ffprobe " + filename).splitlines():
        match = FFMPEG_INFO_PATTERN.match(line)
        if match:
            ret.append([match.group(1), None])
        elif ret:
            match = FFMPEG_STREAM_TITLE_PATTERN.match(line)
            if match:
                ret[-1][1] = match.group(1)
        elif not title:
            match = FFMPEG_TITLE_PATTERN.match(line)
            if match:
                title = match.group(1)
    return title, ret


def _ffmpeg_info(filename):
    sequences = []
    movie_title, streams = ffmpeg_text_info(filename)
    definitions = [[], [], [], movie_title, sequences]
    for info, title in streams:
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
        definitions[['Video', 'Audio', 'Subtitle'].index(stream_type)].append((seq, language, more, title))
        sequences.append((seq, stream_type, language, more))
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
            _mkvmerge_launch('mkvmerge -i ' + name, name)
    else:
        print _mkvmerge_launch(command, filename)


def _update_file(filename, skip_audio_check, in_recursion=False):
    _info(filename, '')
    video, audio, subtitles, movie_title, sequences = _ffmpeg_info(filename)
    if len(video) != 1:
        _error(filename, "%d video streams" % len(video))
    if not audio:
        _error(filename, "%d audio streams" % len(video))
    final_audios = _sort_audios(filename, audio, skip_audio_check)
    final_videos = _sort_tracks(video, _get_video_key)
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

    created_file = _correct_sequencing(filename, sequences, final_videos, final_audios, final_subs,
                                       _DRY_RUN and not in_recursion)
    if created_file:
        if not _DRY_RUN:
            if in_recursion:
                _error(filename, "After sequencing correction, a second correction is required, not good")
            else:
                _update_file(created_file, skip_audio_check=True, in_recursion=True)
        return

    _do_non_sequencing_corrections(filename, movie_title, first_audio, final_videos, final_audios, final_subs)


def _do_non_sequencing_corrections(filename, movie_title, first_audio, final_videos, final_audios, final_subs):

    corrections = []

    new_title = _suggest_title(filename)
    if new_title != movie_title:
        corrections.append('--set title="%s"' % new_title)

    if final_videos[0][1] != first_audio:
        _info(filename, 'Updating video language to ' + first_audio)  # no warning, just correct it !
        corrections.append('--edit track:%d --set language=%s' % (final_videos[0][0] + 1, first_audio))

    if final_videos[0][3]: # there is title, remove it
        corrections.append('--edit track:%d --set name=' % (final_videos[0][0] + 1))

    for sub in final_subs:
        correct_name = LANGUAGES[sub[1]]
        if sub[-1] == correct_name:
            sub[-1] = None
        else:
            sub[-1] = correct_name

    for seq, _, info, title in final_audios + final_subs:
        subcorrections = []
        if title:
            subcorrections.append('--set name="%s"' % title)
        if '(default)' in info:
            subcorrections.append('--set flag-default=0')
        if '(forced)' in info:
            subcorrections.append('--set flag-forced=0')
        if subcorrections:
            corrections.append('--edit track:%d' % (seq+1))
            corrections.extend(subcorrections)

    if corrections:
        command = 'mkvpropedit %s %s' % (filename, ' '.join(corrections))
        _info(filename, command)
        if not _DRY_RUN:
            _mkvpropedit_launch(filename, command)
    else:
        _info(filename, 'No changes required')


def _suggest_title(filename):
    match = FILENAME_PATTERN.match(os.path.basename(filename))
    if not match:
        _error(filename, 'Name of file is not expected')
    name = match.group(1).replace('_', ' ')
    return '%s (%s)' % (name, match.group(2))


def _check_filename_by_language(filename, language):
    if language != LANG_BY_PRIO[0]:
        try:
            language = LANGUAGES[language]
        except KeyError:
            _error(filename, 'Please add ' + language + ' to variable LANGUAGES_IN_FILENAMES')
        name, ext = os.path.splitext(filename)
        if not name.endswith('_' + language):
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


def _correct_sequencing(filename, original_sequences, videos, audios, subtitles, dry_run):
    final_tracks = [x[0] for x in videos + audios + subtitles]
    final_order = [None] * len(original_sequences)
    for i, s in enumerate(final_tracks):
        final_order[s] = i

    if final_order == range(len(original_sequences)):
        return None

    commands = ['ffmpeg', '-n', '-hide_banner', '-i', filename]

    for track in final_tracks:
        commands.append('-map')
        commands.append('0:%d' % track)

    commands.append('-c:v copy -c:a copy')
    if subtitles:
        commands.append('-c:s copy')

    for order, sequence in zip(final_order, original_sequences):
        track, type, language, info = sequence
        position = ('%02d' % order) if order is not None else '--'
        _info(filename, '%s   (%-10s : %-3s) %s' % (position, type, language, info))

    target_file = _get_target_file(filename)

    command = ' '.join(commands + [target_file])
    _info(filename, command)

    if not dry_run:
        _ffmpeg_launch(command)

    return target_file


def _suggest_audio_name(lang, comment, codec, mode, title, level):
    ret = LANGUAGES[lang]
    if level:
        ret += ' [' + codec
        if level > 1:
            ret += ', ' + mode
        ret += ']'
    if comment:
        ret += ' - Commentary'
        try:
            # add any text after : found in title after the comment
            ret += title[title.index(' - ', title.lower().index('comment')+1):]
        except ValueError:
            pass

    return ret


def _sort_audios(filename, audio_tracks, skip_audio_check):
    """Returns list of (sequence, language, new title)"""
    use = []
    for seq, lang, info, title in audio_tracks:
        codec, freq, mode, rate = _parse_audio_info(filename, info)
        comment = 'comment' in title.lower() if title else False
        # precedence is: comments last, then by language, then preserve current ordering
        precedence = (-int(comment), -_get_lang_key(lang), seq)
        use.append([precedence, seq, lang, info, title, codec, mode, comment, title])

    if not skip_audio_check:
        # we define 3 levels in _suggest_audio_name: only lang, lang + codec, lang + codec + mode
        for level in range(3):
            s = set()
            for u in use:
                u[-1] = _suggest_audio_name(u[2], u[7], u[5], u[6], u[4], level)
                s.add(u[-1])
            if len(s) == len(use):  # more than one track would have the same name
                if level:  # (if level=0, all is good)
                    _warning(filename, 'Multiple audio tracks in same language')
                break
        else:
            _error(filename, 'Multiple audio tracks in same language / codec / mode: ' + ' / '. join(u[-1] for u in use))

    use.sort()
    return [(u[1], u[2], u[3], (None if u[4] and u[4].startswith(u[8]) else u[8])) for u in use]


def _sort_tracks(tracks, key_provider):
    ret, tmp = [], []
    for seq, lang, info, title in sorted(tracks):
        tmp.append([key_provider(lang, info), seq, lang, info, title])
    tmp.sort()
    return [t[1:] for t in tmp]
    #     is_default = '(default)' in info
    #     is_forced = '(forced)' in info
    #     ret.append((seq, lang, is_default, is_forced))
    # return ret


def _get_lang_key(lang):
    try:
        return len(LANG_BY_PRIO) - LANG_BY_PRIO.index(lang)
    except ValueError:
        return 0


def _get_subtitle_key(lang, info):
    return -_get_lang_key(lang)


def _get_video_key(lang, info):
    return _get_lang_key(lang)


def _parse_audio_info(filename, info):
    """Returns audio codec, audio frequency, audio mode, audio rate"""
    s = info.split(',')
    while len(s) < 5:
        s.append('*')
    codec, freq, mode, _, rate = s[:5]
    for c in AUDIO_CODECS_BY_PRIO:
        if c in codec:
            codec = c
            break
    else:
        _warning(filename, 'unexpected audio codec : ' + codec)
        codec = ''
    for c in AUDIO_MODES:
        if c in mode:
            mode = c
            break
    else:
        _warning(filename, 'unexpected audio mode : ' + mode)
        mode = ''
    match = AUDIO_FREQUENCY_PATTERN.match(freq)
    if match:
        freq = match.group(1)
    else:
        _warning(filename, 'unexpected rate : ' + rate)
        freq = '00000'

    match = AUDIO_RATE_PATTERN.match(rate)
    if match:
        rate = match.group(1)
    else:
        rate = ''
    if len(rate) > 5:
        _warning(filename, 'unexpected audio rate:' + rate)
    while len(rate) < 5:
        rate = '0' + rate

    return codec, freq, mode, rate


if __name__ == '__main__':
    import argparse

    clParser = argparse.ArgumentParser(description='Movies curator')
    clParser.add_argument('-t', '--target', default='.', help='location for final files, if required')
    clParser.add_argument('-i', '--info-only', action='store_true', help='short info on the file')
    clParser.add_argument('--go', action='store_true', help='perform the required changes')
    clParser.add_argument('--skip-audio-check', action='store_true', help='avoid audio normalization checks')
    clParser.add_argument('--only-files', action='store_true', help='only check for files')
    clParser.add_argument('--only-folders', action='store_true', help='only check for directories')
    clParser.add_argument('filenames', nargs='+')
    args = clParser.parse_args()

    if args.info_only:
        for each in args.filenames:
            print
            print each
            print '='*len(each)
            title, streams = ffmpeg_text_info(each)
            print 'Title:', (title if title else 'no title')
            for l, title in streams:
                print l
                print '\t\tTitle:', (title if title else 'no title')
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
                    _update_file(each, args.skip_audio_check)
            elif os.path.isdir(each):
                if not args.only_files:
                    _update_dir(each)
            else:
                _warning(each, 'Nothing to do')
