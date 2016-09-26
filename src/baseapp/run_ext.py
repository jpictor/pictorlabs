import time
from datetime import datetime
import subprocess32 as subprocess
import select
from .logging_ext import logger


class RunResult(object):
    def __init__(self, text, status):
        self.text = text
        self.status = status


def run_with_io_timeout(cmd, timeout_sec=120):
    command = ' '.join(cmd)
    logger.info('run_with_io_timeout: running {}'.format(command))

    start_time = datetime.now()

    p = subprocess.Popen(
        cmd, bufsize=0, shell=False,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        close_fds=True)

    process_id = p.pid
    logger.info('run_with_io_timeout: spawned process pid={}'.format(process_id))

    def read_line():
        _ln = ''
        while True:
            _rlist, _wlist, _xlist = select.select([p.stdout], [], [p.stdout], timeout_sec)
            if _xlist:
                return _ln, 'closed'
            if not _rlist:
                return _ln, 'timeout'
            _c = p.stdout.read(1)
            if not _c:
                return _ln, 'closed'
            if _c == '\n':
                return _ln, ''
            _ln += _c

    last_line_time = time.time()
    lines = []
    while True:
        ln, status = read_line()
        lines.append(ln)
        print(ln)
        if status == 'closed':
            break
        ## if ln is none then the read timed out, kill it
        if status == 'timeout':
            p.kill()
            break
        ## save output to the db at 5 second intervals
        if time.time() - last_line_time > 5:
            last_line_time = time.time()

    p.stdout.close()
    p.wait()
    end_time = datetime.now()
    duration_sec = (end_time - start_time).total_seconds()

    if p.returncode == 0:
        logger.info('run_with_io_timeout: return_code={} duration={}sec'.format(p.returncode, duration_sec))
    else:
        if status == 'timeout':
            state = 'killed hung job'
        else:
            state = 'failed'
        logger.error('run_with_io_timeout: return_code={} duration={}sec {}'.format(p.returncode, duration_sec, state))

    return RunResult(u''.join(lines), p.returncode)

