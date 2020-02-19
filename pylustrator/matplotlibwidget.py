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

import qtawesome as qta
from qtpy import QtWidgets, QtCore
from qtpy import API_NAME as QT_API_NAME

if QT_API_NAME.startswith("PyQt4"):
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as Canvas
    from matplotlib.backends.backend_qt4agg import FigureManager
    from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
else:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
    from matplotlib.backends.backend_qt5agg import FigureManager
    from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class MatplotlibWidget(Canvas):
    """
    MatplotlibWidget inherits PyQt4.QtGui.QWidget
    and matplotlib.backend_bases.FigureCanvasBase
    
    Options: option_name (default_value)
    -------    
    parent (None): parent widget
    title (''): figure title
    xlabel (''): X-axis label
    ylabel (''): Y-axis label
    xlim (None): X-axis limits ([min, max])
    ylim (None): Y-axis limits ([min, max])
    xscale ('linear'): X-axis scale
    yscale ('linear'): Y-axis scale
    width (4): width in inches
    height (3): height in inches
    dpi (100): resolution in dpi
    hold (False): if False, figure will be cleared each time plot is called
    
    Widget attributes:
    -----------------
    figure: instance of matplotlib.figure.Figure
    axes: figure axes
    
    Example:
    -------
    self.widget = MatplotlibWidget(self, yscale='log', hold=True)
    from numpy import linspace
    x = linspace(-10, 10)
    self.widget.axes.plot(x, x**2)
    self.wdiget.axes.plot(x, x**3)
    """
    def __init__(self, parent=None, num=1, title='', xlabel='', ylabel='',
                 xlim=None, ylim=None, xscale='linear', yscale='linear',
                 size=None, dpi=100):
        self.figure = Figure(figsize=size, dpi=dpi)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title(title)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        if xscale is not None:
            self.axes.set_xscale(xscale)
        if yscale is not None:
            self.axes.set_yscale(yscale)
        if xlim is not None:
            self.axes.set_xlim(*xlim)
        if ylim is not None:
            self.axes.set_ylim(*ylim)

        Canvas.__init__(self, self.figure)
        self.setParent(parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.updateGeometry()
        
        self.manager = FigureManager(self, 1)
        self.manager._cidgcf = self.figure
        
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
    signal = QtCore.Signal()

    def __init__(self, num="", *args, **kwargs):
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("Figure %s" % num)
        self.setWindowIcon(qta.icon("fa.bar-chart"))
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.canvas = MatplotlibWidget(self, *args, **kwargs)
        self.canvas.window = self
        self.layout.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.layout.addWidget(self.toolbar)

        self.signal.connect(self.show)

    def scheduleShow(self):
        self.signal.emit()
