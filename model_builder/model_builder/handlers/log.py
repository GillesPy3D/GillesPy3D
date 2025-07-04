'''
GillesPy3D is a platform for simulating biochemical systems
Copyright (C) 2025 GillesPy3D developers.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import sys
import logging
from tornado.log import LogFormatter

log = logging.getLogger('gillespy3d')
spy_log = logging.getLogger('SpatialPy')

def init_log():
    '''
    Initialize the GillesPy3D logger

    Attributes
    ----------
    '''
    relocate_old_logs()
    setup_stream_handler()
    setup_file_handler()
    setup_spy_file_handler()
    log.setLevel(logging.DEBUG)
    log.propagate = False


def relocate_old_logs():
    '''
    Move the user log file to its new location (/var/log).
    '''
    user_dir = os.path.expanduser("~")
    src = os.path.join(user_dir, ".user-logs.txt")
    if not os.path.exists(src):
        return

    src_size = os.path.getsize(src)
    if src_size < 500000:
        return

    with open(src, "r") as log_file:
        logs = log_file.read().rstrip().split('\n')
    
    mlog_size = src_size % 500000
    mlogs = [logs.pop()]
    while sys.getsizeof("\n".join(mlogs)) < mlog_size:
        mlogs.insert(0, logs.pop())
    with open(os.path.join(user_dir, ".user-logs.txt"), "w") as main_log_file:
        main_log_file.write("\n".join(mlogs))

    blogs = [logs.pop()]
    nlog_size = sys.getsizeof(f"\n{logs[-1]}")
    while logs and sys.getsizeof("\n".join(blogs)) + nlog_size < 500000:
        blogs.insert(0, logs.pop())
        nlog_size = sys.getsizeof(f"\n{logs[-1]}")
    with open(os.path.join(user_dir, ".user-logs.txt.bak"), "w") as backup_log_file:
        backup_log_file.write("\n".join(blogs))


def setup_stream_handler():
    '''
    Initialize the GillesPy3D stream handler

    Attributes
    ----------
    '''
    handler = logging.StreamHandler()
    fmt = '%(color)s[%(levelname)1.1s %(asctime)s GillesPy3D '
    fmt += '%(filename)s:%(lineno)d]%(end_color)s %(message)s'
    formatter = LogFormatter(fmt=fmt, datefmt='%H:%M:%S', color=True)
    handler.setFormatter(formatter)
    handler.setLevel(logging.WARNING)
    log.addHandler(handler)


def setup_file_handler():
    '''
    Initialize the GillesPy3D file handler

    Attributes
    ----------
    '''
    def namer(name):
        '''
        Namer function for the RotatingFileHandler

        Attributes
        ----------
        name : str
            Default name of the log file.
        '''
        return f"{name}.bak"

    def rotator(src, dst):
        '''
        Rotator function for the RotatingFileHandler

        Attributes
        ----------
        src : str
            Path to the main log file.
        dst : str
            Path to the backup log file.
        '''
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
        os.remove(src)

    fmt = '%(asctime)s$ %(message)s'
    formatter = LogFormatter(fmt=fmt, datefmt="%b %d, %Y  %I:%M %p UTC")

    path = os.path.join(os.path.expanduser("~"), ".user-logs.txt")
    handler = logging.handlers.RotatingFileHandler(path, maxBytes=500000, backupCount=1)
    handler.namer = namer
    handler.rotator = rotator
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    log.addHandler(handler)


def setup_spy_file_handler():
    '''
    Initialize the SpatialPy file handler

    Attributes
    ----------
    '''
    print(spy_log.handlers)
    fmt = '%(asctime)s$ %(message)s'
    formatter = LogFormatter(fmt=fmt, datefmt="%b %d, %Y  %I:%M %p UTC")

    path = os.path.join(os.path.expanduser("~"), ".user-logs.txt")
    handler = logging.FileHandler(path)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    spy_log.addHandler(handler)
