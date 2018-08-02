#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
