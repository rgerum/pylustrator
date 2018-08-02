#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division
import os
import sys


def check_for_uncommited_changes():
    uncommited = os.popen("hg status -m").read().strip()
    if uncommited != "":
        print(uncommited, file=sys.stderr)
        print("ERROR: uncommitted changes in repository.", os.getcwd(), file=sys.stderr)
        sys.exit(1)
    os.system("hg pull -u")


def replace_version(file, version_old, version_new):
    print("changing version number in", file)
    with open(file, "r") as fp:
        data = fp.readlines()
    with open(file, "w") as fp:
        for line in data:
            fp.write(line.replace(version_old, version_new))


def get_current_version():
    # get the directory of the repository
    parent_dir = os.path.join(os.path.dirname(__file__), "..")

    # go to parent directory
    os.chdir(parent_dir)

    sys.path.insert(0, parent_dir)
    import pylustrator
    current_version = pylustrator.__version__

    return current_version