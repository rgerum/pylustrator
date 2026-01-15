#!/usr/bin/env python
# -*- coding: utf-8 -*-
# matplotlibwidget.py

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

"""
MatplotlibWidget
================

Example of matplotlib widget for PyQt4

Copyright © 2009 Pierre Raybaut
This software is licensed under the terms of the MIT License

Derived from 'embedding_in_pyqt4.py':
Copyright © 2005 Florent Rougon, 2006 Darren Dale
"""

__version__ = "1.0.0"

import time
from typing import TYPE_CHECKING

import qtawesome as qta

if TYPE_CHECKING:
    from PyQt5 import QtWidgets, QtCore
    from PyQt5.QtCore import pyqtSignal as Signal
else:
    from qtpy import QtWidgets, QtCore
    from qtpy.QtCore import Signal

try:  # for matplotlib > 3.0
    from matplotlib.backends.backend_qtagg import (
        FigureCanvas,  # ty:ignore[unresolved-import]
        FigureManager,  # ty:ignore[unresolved-import]
        NavigationToolbar2QT as NavigationToolbar,
    )
except ModuleNotFoundError:
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas,  # ty:ignore[unresolved-import]
        FigureManager,  # ty:ignore[unresolved-import]
        NavigationToolbar2QT as NavigationToolbar,
    )
from matplotlib.figure import Figure


class MatplotlibWidget(FigureCanvas):
    quick_draw = True
    window_pylustrator = None  # "PlotLayout" | None = None

    def __init__(self, parent=None, figure=None, *args, **kwargs):
        if figure is None:
            self.figure = Figure(*args, **kwargs)
        else:
            self.figure = figure

        super().__init__(self.figure)
        self.setParent(parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.updateGeometry()

        self.manager = FigureManager(self, 1)
        self.manager._cidgcf = self.figure

        self.timer = QtCore.QTimer()
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.draw)

    timer: QtCore.QTimer | None = None

    def schedule_draw(self):
        if self.quick_draw is True:
            return super().draw()
        if self.timer and not self.timer.isActive():
            self.timer.start()

    def draw(self):
        if self.timer:
            self.timer.stop()
        # import traceback
        # print(traceback.print_stack())
        t = time.time()
        super().draw()
        duration = time.time() - t
        # if drawing is slow delay the drawing a bit to create a more smooth experience
        if duration > 0.1:
            self.quick_draw = False
        else:
            self.quick_draw = True

    def show(self):
        self.draw()

    def sizeHint(self):
        w, h = self.get_width_height()
        return QtCore.QSize(w, h)

    def minimumSizeHint(self):
        return QtCore.QSize(10, 10)


def make_pickelable(cls):
    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__init__()

    cls.__getstate__ = __getstate__
    cls.__setstate__ = __setstate__


try:
    make_pickelable(NavigationToolbar)
    make_pickelable(MatplotlibWidget)
except AttributeError:
    pass


class CanvasWindow(QtWidgets.QWidget):
    signal = Signal()

    def __init__(self, num="", *args, **kwargs):
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("Figure %s" % num)
        self.setWindowIcon(qta.icon("fa5s.bar-chart"))
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        self.canvas = MatplotlibWidget(self, *args, **kwargs)
        self.canvas.window = self
        self.layout_main.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout_main.addWidget(self.toolbar)

        self.signal.connect(self.show)

    def scheduleShow(self):
        self.signal.emit()
