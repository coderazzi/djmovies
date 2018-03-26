#!/usr/bin/env python

import logging
import os
import re
import subprocess
import sys
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

REMOVE_TRACK_SIGNATURE = 'TO-REMOVE'

MAX_TIME_FMPEG_INFO = 30  # 30 seconds
MAX_TIME_MUX = 3600  # 60 minutes
FFMPEG_INFO_PATTERN = re.compile('^\s+Stream #(.+)$')
FFMPEG_STREAM_TITLE_PATTERN = re.compile('^\s+title\s+:\s+(.+)$')
FFMPEG_TITLE_PATTERN = re.compile('^    title\s+:\s+(.+)$')
FFMPEG_INFO_SPECIFIC_PATTERN = re.compile('^(\d+):(\d+)(?:\((\w+)\))?: (Video|Audio|Subtitle|Attachment):(.*)$')
LANG_BY_PRIO = ['en', 'es', 'de', 'fr', 'pt', 'it']
AVOID_SUBTITLES = set()  # ['es'])
SUBTITLES_LANGS_FORCED = ['en']
AUDIO_CODECS = ['ac3', 'dts-hd', 'dts', 'flac', 'vorbis', 'aac']
CONVERTABLE_AUDIO_CODECS = set(['dts-hd', 'dts', 'flac'])
BASIC_AUDIO_CODEC = set(['ac3', 'aac'])
AUDIO_MODES = ['5.1', 'stereo', 'mono', '6.1', '7.1']
AUDIO_FREQUENCY_PATTERN = re.compile('^\s*(\\d\\d\\d\\d\\d) hz\s*$')
AUDIO_RATE_PATTERN = re.compile('^\s*(\\d+) kb/s')
FILENAME_PATTERN = re.compile('(.*?)__(\d\d\d\d)(?:_\w+)?(?:_\w+)?\.\w+$')

TARGET_VIDEO_EXTENSION = '.mkv'
VIDEO_EXTENSIONS = ['.mkv', '.avi', '.mp4']
SUBTITLE_EXTENSIONS = ['.srt', '.idx']
DISMISS_EXTENSIONS = ['.sub']
SUBTITLES_LANGUAGES = {'.en': 'en', '.es': 'es', '.de': 'de', '.fr': 'fr'}

# https://www.loc.gov/standards/iso639-2/php/code_list.php
CONVERT_LANGUAGES = {'eng': 'en', 'fre': 'fr', 'esp': 'es', 'ger': 'de', 'por': 'pt', 'spa': 'es', 'deu': 'de',
                     'fra': 'fr', 'ita': 'it'}
LANGUAGES = {'es': 'Spanish', 'de': 'German', 'jpn': 'Japanese', 'swe': 'Swedish', 'fr': 'French', 'en': 'English',
             'pt': 'Portuguese', 'cat': 'Cat', 'kor': 'Korean', 'it': 'Italian', 'heb': 'Hebrew', 'chi': 'Chinese',
             'tur': 'Turkish', 'rus': 'Russian', 'hin': 'Hindi', 'nor': 'Norwegian'}


_COMM_KILL = 1
_COMM_FINISHED = 2
_COMM_KILLED = 3

_DRY_RUN = False # note: is not constant
_TARGET_DIR = None


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


def _mkvmerge_launch(command, name_if_error):
    rc, out, _ = _shell(command, MAX_TIME_MUX)
    if rc > 1:
        _error(name_if_error, 'SHELL: ' + out)
    return out


def _mkvpropedit_launch(command, name_if_error):
    rc, out, err = _shell(command, MAX_TIME_MUX)
    if rc:
        _error(name_if_error, 'SHELL: ' + out)


def _ffmpeg_launch(command):
    rc, out, err = _shell(command, MAX_TIME_MUX)
    if rc > 0:
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
        if stream_type == 'Attachment':
            stream_type, language = 'Subtitle', 'tur'
            more = 'Attachment ' + REMOVE_TRACK_SIGNATURE
        elif not language and stream_type != 'Video':
            _error(filename, info + ' ---> missing language')
        if stream != '0':
            _error(filename, info + ' ---> missing stream ' + stream + " : expected '0'")
        seq = int(sequence)
        if language and language not in LANG_BY_PRIO:
            try:
                language = CONVERT_LANGUAGES[language]
            except KeyError:
                pass
        definitions[['Video', 'Audio', 'Subtitle'].index(stream_type)].append((seq, language, more, title))
        sequences.append((seq, stream_type, language, more))
    return definitions


def _invert_language_convert(lang):
    for k, v in CONVERT_LANGUAGES.items():
        if v == lang:
            return k
    return lang


def _get_target_file(base):
    global _TARGET_DIR
    if not _TARGET_DIR:
        if not _DRY_RUN:
            _error(base, 'Operation requires user to specify a --target parameter')
        _TARGET_DIR = '/tmp'
    base, ext = os.path.splitext(os.path.basename(base))
    ret = os.path.abspath(os.path.join(_TARGET_DIR, base + TARGET_VIDEO_EXTENSION))
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
                        subtitles.append((_get_lang_prio(lang_extension), fullname, lang_extension))
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
    _info(filename, command)
    if _DRY_RUN:
        for _, name, _ in subtitles:
            _mkvmerge_launch('mkvmerge -i ' + name, name)
    else:
        _mkvmerge_launch(command, filename)


def _update_file(filename, skip_audio_check, dismiss_extra_videos, add_aac_codec):
    _info(filename, '')
    final_videos, audios, subtitles, movie_title, sequences = _ffmpeg_info(filename)

    if len(final_videos) != 1:
        if dismiss_extra_videos and final_videos:
            _warning(filename, "%d video streams" % len(final_videos))
            final_videos = final_videos[:1]
        else:
            _error(filename, "%d video streams" % len(final_videos))

    final_audios_extended = _sort_audios(filename, audios, skip_audio_check)
    final_audios = [e[:-2] for e in final_audios_extended]
    if not final_audios:
        _error(filename, "%d audio streams" % len(final_audios))

    final_subs = _sort_subtitles(subtitles, final_audios)
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
                                       not _DRY_RUN and not add_aac_codec)
    if created_file:
        if add_aac_codec:
            _error(filename, "Cannot add aac codec if file requires modification")
        return

    mod = _do_non_sequencing_corrections(filename, movie_title, first_audio, final_videos, final_audios, final_subs)

    if add_aac_codec:
        if mod:
            _error(filename, 'Requested to add aac, but file required modifications')
        else:
            _add_aac_codec(filename, first_audio, final_videos, final_audios_extended, final_subs)
    elif not mod:
        _info(filename, 'No changes required')


def _add_aac_codec(filename, first_audio, videos, audios, subs):
    use, position = None, 0
    for seq, lang, _, _, codec, comment in audios:
        if lang == first_audio and not comment:
            position = max(position, seq)
            if codec in CONVERTABLE_AUDIO_CODECS:
                if use is None:
                    use = seq, codec
            if codec in BASIC_AUDIO_CODEC:
                _info(filename, 'Has already codec ' + codec + ': not enhancing required')
                return False
    if use is None:
        _error(filename, 'Cannot add aac')
    else:
        _info(filename, 'Adding aac from track %d [%s]' % use)

    target = _get_target_file(filename)
    aac_target = _get_target_file(filename + '.aac')

    seqs = [s[0] for s in videos + audios + subs]
    index = seqs.index(position) + 1
    seqs = ['-map 0:%d' % s for s in seqs]
    seqs.insert(index, '-map 1:0')

    # first step: extract audio as AAC : ffmpeg -i /Volumes/MOVIES_IV/Sleeping_Beauty__1959.mkv -map 0:1 -c:a aac kk.aac
    commandA = 'ffmpeg -n -hide_banner -i %s -map 0:%d -c:a aac %s' % (filename, use[0], aac_target)

    # second step: merge movie and this audio: ffmpeg -i /Volumes/MOVIES_IV/Sleeping_Beauty__1959.mkv -i kk.aac
    #   -map 0:0 -map 1:0 -map 0:1 -map 0:2 -map 0:3 -map 0:4 -c copy -metadata:s:a:0 language=en
    #   /Volumes/TTC/__MOVIES/Sleeping_Beauty__1959.mkv
    commands = ['ffmpeg -n -hide_banner -i %s -i %s' % (filename, aac_target)]
    commands.extend(seqs)
    commands.append('-c copy -metadata:s:%d language=%s %s' % (index, _invert_language_convert(first_audio), target))
    commandB = ' '.join(commands)

    if _DRY_RUN:
        _info(filename, commandA)
        _info(filename, commandB)
    else:

        if os.path.exists(target):
            _error(target, 'Target file already exists, coward exit...')
        if os.path.exists(aac_target):
            _error(aac_target, 'AAC file already exists, coward exit...')

        _info(filename, commandA)
        try:
            _ffmpeg_launch(commandA)
        except Exit:
            logging.error("Cannot handle this file: aac cannot be extracted")
            return

        _info(filename, commandB)
        _ffmpeg_launch(commandB)

        # third step: normalize file
        _update_file(target, skip_audio_check=False, dismiss_extra_videos=False, add_aac_codec=False)


def _do_non_sequencing_corrections(filename, movie_title, first_audio, final_videos, final_audios, final_subs):

    corrections = []

    new_title = _suggest_title(filename)
    if new_title != movie_title:
        corrections.append('--set title="%s"' % new_title)

    if final_videos[0][1] != first_audio:
        corrections.append('--edit track:%d --set language=%s' % (final_videos[0][0] + 1, first_audio))

    if final_videos[0][3]: # there is title, remove it
        corrections.append('--edit track:%d --set name=' % (final_videos[0][0] + 1))

    for sub in final_subs:
        correct_name = _get_language_from_code(sub[1])
        if sub[-1] == correct_name:
            sub[-1] = None
        else:
            sub[-1] = correct_name

    i, first_sub = 0, len(final_audios)
    for seq, lang, info, title in final_audios + final_subs:
        subcorrections = []
        if title:
            subcorrections.append('--set name="%s"' % title)
        is_default = '(default)' in info
        if i == first_sub and first_audio != 'es':
            if lang == 'en' or lang == first_audio:
                if not is_default:
                    subcorrections.append('--set flag-default=1')
            elif is_default:
                subcorrections.append('--set flag-default=0')
        elif is_default:
            subcorrections.append('--set flag-default=0')

        if '(forced)' in info:
            subcorrections.append('--set flag-forced=0')
        i = i+1
        if subcorrections:
            corrections.append('--edit track:%d' % (seq+1))
            corrections.extend(subcorrections)

    if corrections:
        command = 'mkvpropedit %s %s' % (filename, ' '.join(corrections))
        _info(filename, command)
        if not _DRY_RUN:
            _mkvpropedit_launch(command, filename)

    return corrections


def _suggest_title(filename):
    match = FILENAME_PATTERN.match(os.path.basename(filename))
    if not match:
        _error(filename, 'Name of file is not expected')
    name = match.group(1).replace('_', ' ')
    return ('%s (%s)' % (name, match.group(2))).strip()


def _check_filename_by_language(filename, language):
    if language != LANG_BY_PRIO[0]:
        language = _get_language_from_code(language)
        name, ext = os.path.splitext(filename)
        if not name.endswith('_' + language):
            _warning(filename, 'should end in __' + language)
            suggestion = os.path.join(os.path.dirname(filename), os.path.basename(name))+ '_' + language
            _error(filename, 'mv ' + filename + ' ' + suggestion + ext)


def _get_language_from_code(code):
    try:
        return LANGUAGES[code]
    except KeyError:
        raise Exception('Language %s not found, please extend LANGUAGES variable' % code)


def _correct_sequencing(filename, original_sequences, videos, audios, subtitles, do_it):
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

    if do_it:
        _ffmpeg_launch(command)

    return target_file


def _suggest_audio_name(lang, comment, codec, mode, title, level):
    ret = _get_language_from_code(lang)
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


def _is_comment(track_info):
    return 'comment' in track_info.lower() if track_info else False


def _sort_audios(filename, audio_tracks, skip_audio_check):
    """Returns list of (sequence, language, new title)"""
    use, codecs = [], set()
    for seq, lang, info, title in audio_tracks:
        if title and REMOVE_TRACK_SIGNATURE in title:
            continue
        codec, freq, mode, rate = _parse_audio_info(filename, info)
        comment = _is_comment(title)
        if not comment:
            codecs.add(codec)
        # precedence is: comments last, then by language, then preserve current ordering
        precedence = (int(comment), _get_lang_prio(lang), seq)
        use.append([precedence, seq, lang, info, title, codec, mode, comment, title])

    if not codecs.intersection(BASIC_AUDIO_CODEC):
        _warning(filename, 'No basic audio formats support: ' + ','.join(codecs))
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
    return [(u[1], u[2], u[3], (None if u[4] == u[8] else u[8]), not u[7] and u[5], u[7]) for u in use]


def _sort_subtitles(subtitles, final_audios):
    # the only subtitles we will return are those in the final_audios, plus English, Spanish
    # the order will be as well those in the audios, plus again English and Spanish
    langs = [lang for _, lang, _, _ in final_audios if lang in LANG_BY_PRIO and lang not in AVOID_SUBTITLES]
    langs = langs + SUBTITLES_LANGS_FORCED

    ret, tmp = [], []
    for seq, lang, info, title in subtitles:
        if not title or REMOVE_TRACK_SIGNATURE not in title:
            try:
                tmp.append([langs.index(lang), seq, lang, info, title])
            except ValueError:
                pass

    tmp.sort()
    return [t[1:] for t in tmp]


def _get_lang_prio(lang, priorities=LANG_BY_PRIO):
    try:
        return priorities.index(lang)
    except ValueError:
        return len(LANG_BY_PRIO)


def _parse_audio_info(filename, info):
    """Returns audio codec, audio frequency, audio mode, audio rate"""
    s = info.lower().split(',')
    while len(s) < 5:
        s.append('*')
    codec, freq, mode, _, rate = s[:5]
    for c in AUDIO_CODECS:
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


def print_info(filename):
    print
    print filename
    print '='*len(filename)
    title, streams = ffmpeg_text_info(filename)
    print 'Title:', (title if title else 'no title')
    for l, title in streams:
        print l
        print '\t\tTitle:', (title if title else 'no title')
    print


def get_subtitles(filename):
    return [x[3] for x in _ffmpeg_info(filename)[2]]


def main(parser, sysargs):
    global _DRY_RUN, _TARGET_DIR

    args = parser.parse_args(sysargs)

    if args.info_only:
        if (args.target or args.subtitles or args.go or args.skip_audio_check or args.only_files or args.add_aac
                or args.only_folders or args.dismiss_extra_videos):
            parser.print_help()
            sys.exit(0)
        for each in args.filenames:
            if os.path.isfile(each):
                print_info(each)
    elif args.subtitles:
        if (args.target or args.go or args.skip_audio_check or args.only_files or args.add_aac
                or args.only_folders or args.dismiss_extra_videos):
            parser.print_help()
            sys.exit(0)
        all, l = [], 0
        for each in args.filenames:
            if os.path.isfile(each):
                name = os.path.basename(each)
                all.append((name, get_subtitles(each)))
                l = max(l, len(name))
        format = '%%-%ds   :   ' % l
        for name, subs in all:
            if None in subs:
                _warning(name, 'Subtitles wrong, either normalize it or set name on subtitle streams: mkvpropedit %s --edit track:4 --set name=English' % name)
                subs = [s for s in subs if s]
            print format % name, ','.join(subs)
    else:
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
        for each in args.filenames:
            try:
                if os.path.isfile(each):
                    if not args.only_folders:
                        _update_file(each, args.skip_audio_check, args.dismiss_extra_videos, args.add_aac)
                elif os.path.isdir(each):
                    if args.add_aac:
                        _error(each, 'Cannot use add-aac on directories')
                    if not args.only_files:
                        _update_dir(each)
                else:
                    _warning(each, 'Nothing to do')
            except Exit:
                if not _DRY_RUN:
                    sys.exit(0)


if __name__ == '__main__':
    import argparse

    clParser = argparse.ArgumentParser(description='Movies curator')
    clParser.add_argument('-t', '--target', help='location for final files, if required')
    clParser.add_argument('-i', '--info-only', action='store_true', help='short info on the file')
    clParser.add_argument('--subtitles', action='store_true', help='only show subtitles information')
    clParser.add_argument('--go', action='store_true', help='perform the required changes')
    clParser.add_argument('--add-aac', action='store_true', help='adds support for aac audio codec')
    clParser.add_argument('--skip-audio-check', action='store_true', help='avoid audio normalization checks')
    clParser.add_argument('--only-files', action='store_true', help='only check for files')
    clParser.add_argument('--dismiss-extra-videos', action='store_true', help='dismiss video streams after first one')
    clParser.add_argument('--only-folders', action='store_true', help='only check for directories')
    clParser.add_argument('filenames', nargs='+')

    if sys.stdin.isatty():
        # not run as tty
        main(clParser, sys.argv[1:])
    else:
        for f in sys.stdin.readlines():
            i = f.strip()
            if i:
                main(clParser, sys.argv[1:] + [i])
