#!/usr/bin/env python
# -*- coding: utf-8 -*-
# send_to_pypi.py

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

from __future__ import division, print_function

import os
import sys

current_folder = os.getcwd()

try:
    # go to parent folder
    os.chdir(os.path.join(os.path.dirname(__file__), ".."))

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pylustrator"))
    import pylustrator

    current_version = pylustrator.__version__

    from argparse import OptionParser

    parser = OptionParser()
    parser.add_option("-u", "--username", action="store", dest="username")
    parser.add_option("-p", "--password", action="store", dest="password")
    (options, args) = parser.parse_args()

    # upgrade twine (used for uploading)
    os.system("pip install twine --upgrade")

    # pack clickpoints
    os.system("python setup.py sdist")

    # the command
    command_string = f"twine upload dist/pylustrator-{current_version}.tar.gz"
    # optionally add the username
    if options.username:
        command_string += f" --username {options.username}"
    # optionally add the password
    if options.password:
        command_string += f" --password {options.password}"
    # print the command string
    print(command_string)
    # and execute it
    os.system(command_string)
finally:
    os.chdir(current_folder)
