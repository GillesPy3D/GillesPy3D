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
import unittest
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '-m', '--mode', default='staging', choices=['staging', 'release'],
    help='Run integration tests in staging mode or release mode.'
)

def run(mode=None):
    ''' Run the integration tests. '''
    from integration_tests import test_gillespy2

    modules = [
        test_gillespy2
    ]

    for module in modules:
        suite = unittest.TestLoader().loadTestsFromModule(module)
        runner = unittest.TextTestRunner(failfast=mode == 'staging', verbosity=1)

        print("Executing: {}".format(module))
        result = runner.run(suite)
        print('=' * 70)
        if not result.wasSuccessful():
            sys.exit(not result.wasSuccessful())

if __name__ == "__main__":
    os.chdir('/model_builder')
    args = parser.parse_args()
    print(os.path.dirname(__file__))

    run(mode=args.mode)
