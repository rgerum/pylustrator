#!/usr/bin/env python
# -*- coding: utf-8 -*-
# QtShortCuts.py

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

from qtpy import QtCore, QtGui, QtWidgets
import numpy as np
import matplotlib as mpl


def getColorFromCoordinates(p):
    desktop = QtWidgets.QApplication.desktop()
    pixmap = QtWidgets.QGuiApplication.screens().at(desktop.screenNumber()).grabWindow(desktop.winId(),
                                                                                         p.x(), p.y(), 1, 1)
    i = pixmap.toImage()
    return i.pixel(0, 0)


""" Color Chooser """

class QDragableColor(QtWidgets.QLineEdit):
    color_changed = QtCore.Signal(str)

    def __init__(self, value):
        QtWidgets.QLineEdit.__init__(self, value)
        import matplotlib.pyplot as plt
        self.maps = plt.colormaps()
        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setColor(value, True)

    def getBackground(self):
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        try:
            cmap = plt.get_cmap(self.color)
        except:
            return ""
        text = "background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, "
        N = 10
        for i in range(N):
            i = i / (N - 1)
            text += "stop: %.2f %s, " % (i, mpl.colors.to_hex(cmap(i)))
        text = text[:-2] + ");"
        return text

    def setColor(self, value, no_signal=False):
        # display and save the new color
        self.color = value
        self.setText(value)
        self.color_changed.emit(value)
        if value in self.maps:
            self.setStyleSheet("text-align: center; border: 2px solid black; "+self.getBackground())
        else:
            self.setStyleSheet("text-align: center; background-color: %s; border: 2px solid black" % value)

    def getColor(self):
        # return the color
        return self.color

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            drag.setPixmap(self.grab())
            mime = QtCore.QMimeData()
            mime.setText(self.color)
            drag.setMimeData(mime)
            self.setStyleSheet("background-color: lightgray; border: 2px solid gray")
            self.setDisabled(True)
            self.setText("")
            drag.exec()
            self.setText(self.color)
            self.setDisabled(False)
            if self.color in self.maps:
                self.setStyleSheet("text-align: center; border: 2px solid black; "+self.getBackground())
            else:
                self.setStyleSheet("text-align: center; background-color: %s; border: 2px solid black" % self.color)
        elif event.button() == QtCore.Qt.RightButton:
            self.openDialog()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/plain") and event.source() != self:
            event.acceptProposedAction()
            if self.color in self.maps:
                self.setStyleSheet("border: 2px solid red; "+self.getBackground())
            else:
                self.setStyleSheet("background-color: %s; border: 2px solid red" % self.color)

    def dragLeaveEvent(self, event):
        if self.color in self.maps:
            self.setStyleSheet("border: 2px solid black; "+self.getBackground())
        else:
            self.setStyleSheet("background-color: %s; border: 2px solid black" % self.color)

    def dropEvent(self, event):
        color = event.source().getColor()
        event.source().setColor(self.getColor())
        self.setColor(color)

    def openDialog(self):
        if self.color in self.maps:
            dialog = ColorMapChoose(self.parent(), self.color)
            colormap, selected = dialog.exec()
            print(colormap, selected)
            #return
            #colormap, selected = QtWidgets.QInputDialog.getItem(self.parent(), "Select Colormap", "Colormap:", self.maps,
            #                                                    self.maps.index(self.color), False)
            if selected is False:
                return
            self.setColor(colormap)
        else:
            # get new color from color picker
            qcolor = QtGui.QColor(*np.array(mpl.colors.to_rgb(self.getColor())) * 255)
            color = QtWidgets.QColorDialog.getColor(qcolor, self.parent())
            # if a color is set, apply it
            if color.isValid():
                color = "#%02x%02x%02x" % color.getRgb()[:3]
                self.setColor(color)


from matplotlib import pyplot as plt
import matplotlib as mpl
class ColorMapChoose(QtWidgets.QDialog):
    result = ""

    def __init__(self, parent, map):
        QtWidgets.QDialog.__init__(self, parent)
        main_layout = QtWidgets.QVBoxLayout(self)
        self.layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(self.layout)
        button_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(button_layout)
        self.button_cancel = QtWidgets.QPushButton("Cancel")
        self.button_cancel.clicked.connect(lambda x: self.done(0))
        button_layout.addStretch()
        button_layout.addWidget(self.button_cancel)

        self.maps = plt.colormaps()
        self.buttons = []
        self.setWindowTitle("Select colormap")

        # Have colormaps separated into categories:
        # http://matplotlib.org/examples/color/colormaps_reference.html
        cmaps = [('Perceptually Uniform Sequential', [
            'viridis', 'plasma', 'inferno', 'magma']),
                 ('Sequential', [
                     'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                     'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                     'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']),
                 ('Sequential (2)', [
                     'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone', 'pink',
                     'spring', 'summer', 'autumn', 'winter', 'cool', 'Wistia',
                     'hot', 'afmhot', 'gist_heat', 'copper']),
                 ('Diverging', [
                     'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu',
                     'RdYlBu', 'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic']),
                 ('Qualitative', [
                     'Pastel1', 'Pastel2', 'Paired', 'Accent',
                     'Dark2', 'Set1', 'Set2', 'Set3',
                     'tab10', 'tab20', 'tab20b', 'tab20c']),
                 ('Miscellaneous', [
                     'flag', 'prism', 'ocean', 'gist_earth', 'terrain', 'gist_stern',
                     'gnuplot', 'gnuplot2', 'CMRmap', 'cubehelix', 'brg', 'hsv',
                     'gist_rainbow', 'rainbow', 'jet', 'nipy_spectral', 'gist_ncar'])]

        for cmap_category, cmap_list in cmaps:
            layout = QtWidgets.QVBoxLayout(self)
            label = QtWidgets.QLabel(cmap_category)
            layout.addWidget(label)
            label.setFixedWidth(150)
            for cmap in cmap_list:
                button = QtWidgets.QPushButton(cmap)
                button.setStyleSheet("text-align: center; border: 2px solid black; "+self.getBackground(cmap))
                button.clicked.connect(lambda x, cmap=cmap: self.buttonClicked(cmap))
                self.buttons.append(button)
                layout.addWidget(button)
            layout.addStretch()
            self.layout.addLayout(layout)

    def buttonClicked(self, text):
        self.result = text
        self.done(1)

    def exec(self):
        result = QtWidgets.QDialog.exec(self)
        return self.result, result == 1

    def getBackground(self, color):
        import matplotlib.pyplot as plt
        import matplotlib as mpl
        try:
            cmap = plt.get_cmap(color)
        except:
            return ""
        text = "background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, "
        N = 10
        for i in range(N):
            i = i / (N - 1)
            text += "stop: %.2f %s, " % (i, mpl.colors.to_hex(cmap(i)))
        text = text[:-2] + ");"
        return text


def AddQColorChoose(layout, text, value=None, strech=False):
    # add a layout
    horizontal_layout = QtWidgets.QHBoxLayout()
    layout.addLayout(horizontal_layout)
    # add a text
    # text = QtWidgets.QLabel(text)
    button = QtWidgets.QPushButton("")

    # button.label = text

    def OpenDialog():
        # get new color from color picker
        qcolor = QtGui.QColor(*np.array(mpl.colors.to_rgb(button.getColor())) * 255)
        color = QtWidgets.QColorDialog.getColor(qcolor)
        # if a color is set, apply it
        if color.isValid():
            color = "#%02x%02x%02x" % color.getRgb()[:3]
            button.setColor(color)
            lineEdit.setText(color)
            try:
                button.color_changed(color)
            except AttributeError:
                pass

    def setColor(value):
        # display and save the new color
        button.setStyleSheet("background-color: %s;" % value)
        button.color = value
        try:
            button.color_changed(value)
        except AttributeError:
            pass

    def getColor():
        # return the color
        return button.color

    def editFinished():
        new_color = lineEdit.text()
        setColor(new_color)

    # default value for the color
    if value is None:
        value = "#FF0000"

    lineEdit = QtWidgets.QLineEdit()
    lineEdit.setFixedWidth(50)
    lineEdit.setText(value)
    # lineEdit.label = text
    lineEdit.editingFinished.connect(editFinished)

    # add functions to button
    button.pressed.connect(OpenDialog)
    button.setColor = setColor
    button.getColor = getColor
    # set the color
    button.setColor(value)
    # add widgets to the layout
    # horizontal_layout.addWidget(text)
    horizontal_layout.addWidget(button)
    horizontal_layout.addWidget(lineEdit)
    # add a strech if requested
    if strech:
        horizontal_layout.addStretch()
    return button