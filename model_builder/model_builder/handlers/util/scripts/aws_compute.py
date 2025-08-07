#!/usr/bin/env python3

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
import argparse

import fcntl

sys.path.append("/model_builder/model_builder/") # pylint: disable=wrong-import-position
sys.path.append("/model_builder/model_builder/handlers/") # pylint: disable=wrong-import-position
from util.model_builder_base import GillesPy3DBase
from handlers.log import init_log

init_log()
log = logging.getLogger("gillespy3d")

class OpenAndLock:
    '''
    Wrapper for open that controls the file lock.
    '''
    def __init__(self, path, *pargs, **kwargs):
        self.file = open(path,*pargs, **kwargs)
        if self.file.writable():
            fcntl.lockf(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            print("File is locked")
            self.file.write(str(os.getpid()))

    def __enter__(self, *pargs, **kwargs):
        return self.file

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        self.file.flush()
        os.fsync(self.file.fileno())
        if self.file.writable():
            fcntl.lockf(self.file, fcntl.LOCK_UN)
            print("File is un-locked")
        self.file.close()
        return exc_type is None

    def close(self, **kwargs):
        '''
        Un-lock and close the file.
        '''
        self.__exit__(**kwargs)


