import subprocess
import threading
import time

DEFAULT_MAX_SHELL_TIMEOUT = 3600  # 60 minutes


def shell(proc_args, max_time):
    running, finished, killed = 0, 1, 2
    process_state = running

    def killer():
        nonlocal process_state
        end_time = time.time() + max_time
        while process_state == running and (time.time() < end_time):
            time.sleep(5)
        if process_state == running:
            proc.kill()
            process_state = finished

    proc = subprocess.Popen(proc_args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    thread = threading.Thread(target=killer)
    thread.setDaemon(True)
    thread.start()
    out, err = proc.communicate()
    killed = process_state == killed
    process_state = finished
    if killed:
        err = "Process auto-killed: " + proc_args
        print(err)
    return proc.returncode, out, err


def mkvpropedit_launch(path, arguments):
    command = 'mkvpropedit %s %s' % (path, arguments)
    rc, out, err = shell(command, DEFAULT_MAX_SHELL_TIMEOUT)
    if rc:
        print('FAILED:', command)
        print(err)
        print(out)
        return False
    return True


def set_movie_title(path, title):
    return mkvpropedit_launch(path, '--edit info --set title="%s"' % title)
