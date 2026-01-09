#!/usr/bin/env python
# -*- coding: utf-8 -*-
# release_tools.py

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
import re
from pathlib import Path


def replace_version(file, version_old, version_new):
    file = Path(file)
    if not file.exists():
        return False
    print("changing version number in", file)
    with file.open("r") as fp:
        data = fp.readlines()
    with file.open("w") as fp:
        for line in data:
            fp.write(line.replace(version_old, version_new))
    return True


def get_setup_properties():
    path = Path(__file__).parent
    for i in range(3):
        setup_file = path / "pyproject.toml"
        if setup_file.exists():
            os.chdir(setup_file.parent)
            with setup_file.open("r") as fp:
                match = re.findall(r"(\w*)=[\"'](.*)[\"']", fp.read())
                if match:
                    return {key: value for key, value in match}
            break
        path = path.parent
