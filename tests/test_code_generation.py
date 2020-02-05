#!/usr/bin/env python
# -*- coding: utf-8 -*-
# change_tracker.py

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

import matplotlib
matplotlib.use('agg')
import unittest
import numpy as np

import sys
import mock
import os
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers
from qtpy import QtCore, QtWidgets, QtGui


""" some magic to prevent PyQt5 from swallowing exceptions """
# Back up the reference to the exceptionhook
sys._excepthook = sys.excepthook
# Set the exception hook to our wrapping function
sys.excepthook = lambda *args: sys._excepthook(*args)


class TestFits(unittest.TestCase):

    def setUp(self):
        self.filename = Path(self.id().split(".")[-1]+".py")
        with self.filename.open("w") as fp:
            fp.write("""
import matplotlib.pyplot as plt
import numpy as np

# now import pylustrator
import pylustrator

# activate pylustrator
pylustrator.start()

# build plots as you normally would
np.random.seed(1)
t = np.arange(0.0, 2, 0.001)
y = 2 * np.sin(np.pi * t)
a, b = np.random.normal(loc=(5., 3.), scale=(2., 4.), size=(100,2)).T
b += a

plt.figure(1)
plt.subplot(131)
plt.plot(t, y)

plt.subplot(132)
plt.plot(a, b, "o")

plt.subplot(133)
plt.bar(0, np.mean(a))
plt.bar(1, np.mean(b))

# show the plot in a pylustrator window
plt.show(hide_window=True)
""")

    def tearDown(self):
        self.filename.unlink()
        tmp_file = Path(str(self.filename)+".tmp")
        if tmp_file.exists():
            tmp_file.unlink()

    def test_fitCamParametersFromObjects(self):
        exec(compile(open(self.filename, "rb").read(), self.filename, 'exec'), globals())

        for figure in _pylab_helpers.Gcf.figs:
            figure = _pylab_helpers.Gcf.figs[figure].canvas.figure
            figure.figure_dragger.select_element(figure.axes[0])

            figure.selection.start_move()
            figure.selection.addOffset((-1, 0), figure.selection.dir)
            figure.selection.end_move()
            figure.change_tracker.save()

        with self.filename.open("r") as fp:
            in_block = False
            found = False
            block = ""
            for line in fp:
                if in_block is True:
                    block += line
                    if line == "plt.figure(1).axes[0].set_position([0.123438, 0.110000, 0.227941, 0.770000])\n":
                        found = True
                if line.startswith("#% start: automatic generated code from pylustrator"):
                    in_block = True
                if line.startswith("#% end: automatic generated code from pylustrator"):
                    in_block = False

        self.assertTrue(found, "Figure movement not correctly written to file")


if __name__ == '__main__':
    unittest.main()


