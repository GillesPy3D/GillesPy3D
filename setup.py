# GillesPy3D is a Python 3 package for simulation of
# spatial/non-spatial deterministic/stochastic reaction-diffusion-advection problems
# Copyright (C) 2023 GillesPy3D developers.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU GENERAL PUBLIC LICENSE Version 3 as
# published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU GENERAL PUBLIC LICENSE Version 3 for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#!/usr/bin/env python3
# =============================================================================
# @file    setup.py
# @brief   GillesPy3D setup file
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/GillesPy3D/GillesPy3D
#
# Note: how to do a PyPI release
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Run the following commands:
#
#   python3 setup.py sdist bdist_wheel
#   twine upload dist/*
#
# =============================================================================


from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.bdist_egg import bdist_egg
from setuptools.command.easy_install import easy_install
from setuptools import Extension
from setuptools.command.build_py import build_py
from setuptools.command.build_ext import build_ext
import os
from os import path


# Read the contents of auxiliary files.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SETUP_DIR = path.dirname(os.path.abspath(__file__))

with open(path.join(SETUP_DIR, 'requirements.txt')) as f:
    reqs = f.read().rstrip().splitlines()

with open(path.join(SETUP_DIR, 'README.md'), 'r', errors = 'ignore') as f:
    readme = f.read()

# The following reads the variables without doing an "import handprint",
# because the latter will cause the python execution environment to fail if
# any dependencies are not already installed -- negating most of the reason
# we're using setup() in the first place.  This code avoids eval, for security.

version = {}
with open(path.join(SETUP_DIR, 'gillespy3d/__version__.py')) as f:
    text = f.read().rstrip().splitlines()
    vars = [line for line in text if line.startswith('__') and '=' in line]
    for v in vars:
        setting = v.split('=')
        version[setting[0].strip()] = setting[1].strip().replace("'", '')


# Configure and compile C extension
libcgillespy3d = Extension(
    name="libcgillespy3d._libcgillespy3d",
    language="c++",
    sources=[
        "libcGillesPy3D/obj/include/libcgillespy3d_wrap.cpp",
    ],
    include_dirs=[
        "libcGillesPy3D/include",
        "libcGillesPy3D/external/ANN/include",
        "libcGillesPy3D/external/Sundials/include",
        "libcGillesPy3D/external/Sundials/cmake-build/default/include",
    ],
    library_dirs=[
        "libcGillesPy3D/lib",
    ],
    libraries=[
        "cgillespy3d",
    ],
)


# Finally, define our namesake.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


setup(name                 = version['__title__'].lower(),
      version              = version['__version__'],
      author               = version['__author__'],
      author_email         = version['__email__'],
      maintainer           = version['__author__'],
      maintainer_email     = version['__email__'],
      license              = version['__license__'],
      url                  = version['__url__'],
      download_url         = version['__download_url__'],
      description          = version['__description__'],
      long_description     = readme,
      long_description_content_type = "text/markdown",
      keywords             = "biochemical simulation, Gillespie algorithm, stochastic simulation, biology, spatial simulation, RDME",
      project_urls         = {
          "Tracker": "https://github.com/GillesPy3D/GillesPy3D/issues",
          "Source" : "https://github.com/GillesPy3D/GillesPy3D",
      },
      packages             = find_packages('.') + ['libcgillespy3d'],
      package_dir={'libcgillespy3d': 'libcGillesPy3D/lib/libcgillespy3d'},
      include_package_data = True,
      install_requires     = reqs,

      ext_modules=[libcgillespy3d],
      classifiers      = [
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3',
          'Topic :: Scientific/Engineering',
          'Topic :: Scientific/Engineering :: Chemistry',
          'Topic :: Scientific/Engineering :: Mathematics',
          'Topic :: Scientific/Engineering :: Medical Science Apps.',
          'Intended Audience :: Science/Research'
      ],
)
