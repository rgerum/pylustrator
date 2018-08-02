#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division
import os
import sys

from release_tools import check_for_uncommited_changes, get_current_version

# get the current version (also changes the directory to the pylustrator directory)
current_version = get_current_version()

# check for uncommitted changes
check_for_uncommited_changes()

# upload to pypi
os.system("pip install twine")
os.system("python setup.py sdist")
os.system("twine upload dist/pylustrator-%s.tar.gz" % (current_version, ))
