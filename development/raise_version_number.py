#!/usr/bin/env python
# -*- coding: utf-8 -*-
# raise_version_number.py

# Copyright (c) 2016-2019, Richard Gerum
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

from __future__ import print_function, division
import os
import sys

from release_tools import check_for_uncommited_changes, replace_version, get_current_version


current_version = get_current_version()

# check for new version name as command line argument
try:
    new_version = sys.argv[1]
except IndexError:
    print("ERROR: no new version number supplied.", file=sys.stderr)
    sys.exit(1)

# check if new version name differs
if current_version == new_version:
    print("ERROR: new version is the same as old version.", file=sys.stderr)
    sys.exit(1)

print("setting version number to", new_version)

# check for uncommitted changes
check_for_uncommited_changes()

# Let's go
replace_version("setup.py", current_version, new_version)
replace_version("docs/conf.py", current_version, new_version)
replace_version("pylustrator/__init__.py", current_version, new_version)

# commit changes
os.system("hg commit -m \"set version to v%s\"" % new_version)
os.system("hg tag \"v%s\"" % new_version)
