#!/usr/bin/env python
# -*- coding: utf-8 -*-
# raise_version_number.py

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

import os
import sys

from release_tools import get_setup_properties, replace_version

properties = get_setup_properties()

current_version = properties["version"]
package_name = properties["name"]

# check for new version name as command line argument
try:
    new_version = sys.argv[1]
except IndexError:
    print(f"ERROR: no new version number supplied. Current {package_name} version is {current_version}", file=sys.stderr)
    sys.exit(1)

# check if new version name differs
if current_version == new_version:
    print(f"ERROR: new {package_name} version {new_version} is the same as old version {current_version}.", file=sys.stderr)
    sys.exit(1)

print(f"setting {package_name} version number from {current_version} to {new_version}")

files = ["setup.py", "meta.yaml", "docs/conf.py", package_name+"/__init__.py"]

# Let's go
for file in files:
    if replace_version(file, current_version, new_version):
        os.system(f"git add {file}")
    
# commit changes
os.system(f"git commit -m \"set version to v{new_version}\"")
os.system(f"git tag \"v{new_version}\"")
