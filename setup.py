#!/usr/bin/env python
# -*- coding: utf-8 -*-
# setup.py

# Copyright (c) 2016-2020, Richard Gerum
#
# This file is part of Pylustrator.
#
# Pylustrator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pylustrator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pylustrator. If not, see <http://www.gnu.org/licenses/>

from setuptools import setup

long_description = ""
try:
    long_description = open('readme.rst').read()
except FileNotFoundError:
    pass

setup(name='pylustrator',
      version="1.1.1",
      description='Adds interactivity to arrange panels in matplotlib',
      long_description=long_description,
      url='https://bitbucket.org/fabry_biophysics/pylustrator',
      license="GPLv3",
      author='Richard Gerum',
      author_email='richard.gerum@fau.de',
      packages=['pylustrator'],
      include_package_data=True,
      install_requires=[
          'natsort',
          'numpy',
          'matplotlib',
          'pyqt5',
          'qtpy',
          'qtawesome',
          'scikit-image'
      ],
      )
