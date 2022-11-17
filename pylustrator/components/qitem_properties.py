#!/usr/bin/env python
# -*- coding: utf-8 -*-
# qitem_properties.py

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
from typing import Any
import numpy as np
from packaging import version

import qtawesome as qta
from matplotlib.backends.qt_compat import QtCore, QtGui, QtWidgets

from matplotlib.axes._subplots import Axes
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure

from pylustrator.change_tracker import getReference
from pylustrator.QLinkableWidgets import QColorWidget, CheckWidget, TextWidget, DimensionsWidget, NumberWidget, ComboWidget


class TextPropertiesWidget(QtWidgets.QWidget):
    stateChanged = QtCore.Signal(int, str)
    noSignal = False
    target_list = None

    def __init__(self, layout: QtWidgets.QLayout):
        """ A widget to edit the properties of a Matplotlib text

        Args:
            layout: the layout to which to add the widget
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.buttons_align = []
        self.align_names = ["left", "center", "right"]
        align_group = QtWidgets.QButtonGroup(self)
        for align in self.align_names:
            button = QtWidgets.QPushButton(qta.icon("fa5s.align-" + align), "")
            button.setToolTip("align "+align)
            button.setCheckable(True)
            button.clicked.connect(lambda x, name=align: self.changeAlign(name))
            self.layout.addWidget(button)
            self.buttons_align.append(button)
            align_group.addButton(button)

        self.button_bold = QtWidgets.QPushButton(qta.icon("fa5s.bold"), "")
        self.button_bold.setCheckable(True)
        self.button_bold.clicked.connect(self.changeWeight)
        self.layout.addWidget(self.button_bold)

        self.button_italic = QtWidgets.QPushButton(qta.icon("fa5s.italic"), "")
        self.button_italic.setCheckable(True)
        self.button_italic.clicked.connect(self.changeStyle)
        self.layout.addWidget(self.button_italic)

        self.button_color = QColorWidget(self.layout)
        self.button_color.valueChanged.connect(self.changeColor)

        self.layout.addStretch()

        self.font_size = QtWidgets.QSpinBox()
        self.layout.addWidget(self.font_size)
        self.font_size.valueChanged.connect(self.changeFontSize)

        self.label = QtWidgets.QPushButton(qta.icon("fa5s.font"), "")  # .pixmap(16))
        self.layout.addWidget(self.label)
        self.label.clicked.connect(self.selectFont)

        #self.button_delete = QtWidgets.QPushButton(qta.icon("fa5s.trash"), "")
        #self.button_delete.clicked.connect(self.delete)
        #self.button_delete.setToolTip("delete")
        #self.layout.addWidget(self.button_delete)

    def convertMplWeightToQtWeight(self, weight: str) -> int:
        """ convert a font weight string to a weight enumeration of Qt """
        weight_dict = {'normal': QtGui.QFont.Normal, 'bold': QtGui.QFont.Bold, 'heavy': QtGui.QFont.ExtraBold,
                       'light': QtGui.QFont.Light, 'ultrabold': QtGui.QFont.Black, 'ultralight': QtGui.QFont.ExtraLight}
        if weight in weight_dict:
            return weight_dict[weight]
        return weight_dict["normal"]

    def convertQtWeightToMplWeight(self, weight: int) -> str:
        """ convert a Qt weight value to a string for use in matmplotlib """
        weight_dict = {QtGui.QFont.Normal: 'normal', QtGui.QFont.Bold: 'bold', QtGui.QFont.ExtraBold: 'heavy',
                       QtGui.QFont.Light: 'light', QtGui.QFont.Black: 'ultrabold', QtGui.QFont.ExtraLight: 'ultralight'}
        if weight in weight_dict:
            return weight_dict[weight]
        return "normal"

    def selectFont(self):
        """ open a font select dialog """
        font0 = QtGui.QFont()
        font0.setFamily(self.target.get_fontname())
        font0.setWeight(self.convertMplWeightToQtWeight(self.target.get_weight()))
        font0.setItalic(self.target.get_style() == "italic")
        font0.setPointSizeF(int(self.target.get_fontsize()))
        font, x = QtWidgets.QFontDialog.getFont(font0, self)

        for element in self.target_list:
            element.set_fontname(font.family())
            element.figure.change_tracker.addNewTextChange(element)

            if font.weight() != font0.weight():
                weight = self.convertQtWeightToMplWeight(font.weight())
                element.set_weight(weight)
                element.figure.change_tracker.addNewTextChange(element)

            if font.pointSizeF() != font0.pointSizeF():
                element.set_fontsize(font.pointSizeF())
                element.figure.change_tracker.addNewTextChange(element)

            if font.italic() != font0.italic():
                style = "italic" if font.italic() else "normal"
                element.set_style(style)
                element.figure.change_tracker.addNewTextChange(element)

        self.target.figure.canvas.draw()
        self.setTarget(self.target_list)

    def setTarget(self, element: Artist):
        """ set the target artist for this widget """
        if isinstance(element, list):
            self.target_list = element
            element = element[0]
        else:
            if element is None:
                self.target_list = []
            else:
                self.target_list = [element]
        self.target = None
        self.font_size.setValue(int(element.get_fontsize()))

        index_selected = self.align_names.index(element.get_ha())
        for index, button in enumerate(self.buttons_align):
            button.setChecked(index == index_selected)

        self.button_bold.setChecked(element.get_weight() == "bold")
        self.button_italic.setChecked(element.get_style() == "italic")
        self.button_color.setColor(element.get_color())

        self.target = element

    def delete(self):
        """ delete the target text """
        if self.target is not None:
            fig = self.target.figure
            fig.change_tracker.removeElement(self.target)
            self.target = None
            # self.target.set_visible(False)
            fig.canvas.draw()

    def changeWeight(self, checked: bool):
        """ set bold or normal """
        if self.target:
            element = self.target
            self.target = None

            for element in self.target_list:
                element.set_weight("bold" if checked else "normal")

                element.figure.change_tracker.addNewTextChange(element)

            self.target = element
            self.target.figure.canvas.draw()

    def changeStyle(self, checked: bool):
        """ set italic or normal """
        if self.target:
            element = self.target
            self.target = None

            for element in self.target_list:
                element.set_style("italic" if checked else "normal")

                element.figure.change_tracker.addNewTextChange(element)

            self.target = element
            self.target.figure.canvas.draw()

    def changeColor(self, color: str):
        """ set the text color """
        if self.target:
            element = self.target
            self.target = None

            for element in self.target_list:
                element.set_color(color)
                element.figure.change_tracker.addNewTextChange(element)

            self.target = element
            self.target.figure.canvas.draw()

    def changeAlign(self, align: str):
        """ set the text algin """
        if self.target:
            element = self.target
            self.target = None

            for element in self.target_list:
                index_selected = self.align_names.index(align)
                for index, button in enumerate(self.buttons_align):
                    button.setChecked(index == index_selected)
                element.set_ha(align)
                element.figure.change_tracker.addNewTextChange(element)

            self.target = element
            self.target.figure.canvas.draw()

    def changeFontSize(self, value: int):
        """ set the font size """
        if self.target:
            for element in self.target_list:
                element.set_fontsize(value)
                element.figure.change_tracker.addNewTextChange(element)
            self.target.figure.canvas.draw()


class TextPropertiesWidget2(QtWidgets.QWidget):
    stateChanged = QtCore.Signal(int, str)
    propertiesChanged = QtCore.Signal()
    noSignal = False
    target_list = None

    def __init__(self, layout: QtWidgets.QLayout):
        """ A widget to edit the properties of a Matplotlib text

        Args:
            layout: the layout to which to add the widget
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.buttons_align = []
        self.align_names = ["left", "center", "right"]
        align_group = QtWidgets.QButtonGroup(self)
        for align in self.align_names:
            button = QtWidgets.QPushButton(qta.icon("fa5s.align-" + align), "")
            button.setCheckable(True)
            button.clicked.connect(lambda x, name=align: self.changeAlign(name))
            align_group.addButton(button)
            self.layout.addWidget(button)
            self.buttons_align.append(button)

        self.button_bold = QtWidgets.QPushButton(qta.icon("fa5s.bold"), "")
        self.button_bold.setCheckable(True)
        self.button_bold.clicked.connect(self.changeWeight)
        self.layout.addWidget(self.button_bold)

        self.button_italic = QtWidgets.QPushButton(qta.icon("fa5s.italic"), "")
        self.button_italic.setCheckable(True)
        self.button_italic.clicked.connect(self.changeStyle)
        self.layout.addWidget(self.button_italic)

        self.button_color = QColorWidget(self.layout)
        self.button_color.valueChanged.connect(self.changeColor)

        self.layout.addStretch()

        self.font_size = QtWidgets.QSpinBox()
        self.layout.addWidget(self.font_size)
        self.font_size.valueChanged.connect(self.changeFontSize)

        self.label = QtWidgets.QPushButton(qta.icon("fa5s.font"), "")  # .pixmap(16))
        self.layout.addWidget(self.label)
        self.label.clicked.connect(self.selectFont)

        self.property_names = [
            ("fontsize", "fontsize", int, None),
            ("fontweight", "fontweight", str, None),
            ("color", "color", str, None),
            ("fontstyle", "fontstyle", str, None),
            ("fontname", "fontname", str, None),
            ("horizontalalignment", "horizontalalignment", str, None),
        ]

        self.properties = {}

    def convertMplWeightToQtWeight(self, weight: str) -> int:
        """ convert a font weight string to a weight enumeration of Qt """
        weight_dict = {'normal': QtGui.QFont.Normal, 'bold': QtGui.QFont.Bold, 'heavy': QtGui.QFont.ExtraBold,
                       'light': QtGui.QFont.Light, 'ultrabold': QtGui.QFont.Black, 'ultralight': QtGui.QFont.ExtraLight}
        if weight in weight_dict:
            return weight_dict[weight]
        return weight_dict["normal"]

    def convertQtWeightToMplWeight(self, weight: int) -> str:
        """ convert a Qt weight value to a string for use in matmplotlib """
        weight_dict = {QtGui.QFont.Normal: 'normal', QtGui.QFont.Bold: 'bold', QtGui.QFont.ExtraBold: 'heavy',
                       QtGui.QFont.Light: 'light', QtGui.QFont.Black: 'ultrabold', QtGui.QFont.ExtraLight: 'ultralight'}
        if weight in weight_dict:
            return weight_dict[weight]
        return "normal"

    def selectFont(self):
        """ open a font select dialog """
        font0 = QtGui.QFont()
        font0.setFamily(self.target.get_fontname())
        font0.setWeight(self.convertMplWeightToQtWeight(self.target.get_weight()))
        font0.setItalic(self.target.get_style() == "italic")
        font0.setPointSizeF(int(self.target.get_fontsize()))
        font, x = QtWidgets.QFontDialog.getFont(font0, self)

        self.properties["fontname"] = font.family()
        if font.weight() != font0.weight():
            self.properties["fontweight"] = self.convertQtWeightToMplWeight(font.weight())
        if font.pointSizeF() != font0.pointSizeF():
            self.properties["fontsize"] = font.pointSizeF()
        if font.italic() != font0.italic():
            style = "italic" if font.italic() else "normal"
            self.properties["fontstyle"] = style

        self.propertiesChanged.emit()
        #self.target.figure.canvas.draw()
        self.setTarget(self.target_list)

    def setTarget(self, element: Artist):
        """ set the target artist for this widget """
        if len(element) == 0:
            return
        if isinstance(element, list):
            self.target_list = element
            element = element[0]
        else:
            if element is None:
                self.target_list = []
            else:
                self.target_list = [element]
        self.target = None
        self.font_size.setValue(int(element.get_fontsize()))

        index_selected = self.align_names.index(element.get_ha())
        for index, button in enumerate(self.buttons_align):
            button.setChecked(index == index_selected)

        self.button_bold.setChecked(element.get_weight() == "bold")
        self.button_italic.setChecked(element.get_style() == "italic")
        self.button_color.setColor(element.get_color())

        for name, name2, type_, default_ in self.property_names:
            value = getattr(element, "get_"+name2)()
            self.properties[name] = value

        self.target = element

    def delete(self):
        """ delete the target text """
        if self.target is not None:
            fig = self.target.figure
            fig.change_tracker.removeElement(self.target)
            self.target = None
            # self.target.set_visible(False)
            fig.canvas.draw()

    def changeWeight(self, checked: bool):
        """ set bold or normal """
        self.properties["fontweight"] = "bold" if checked else "normal"
        self.propertiesChanged.emit()

    def changeStyle(self, checked: bool):
        """ set italic or normal """
        self.properties["fontstyle"] = "italic" if checked else "normal"
        self.propertiesChanged.emit()

    def changeColor(self, color: str):
        """ set the text color """
        self.properties["color"] = color
        self.propertiesChanged.emit()

    def changeAlign(self, align: str):
        """ set the text algin """
        self.properties["horizontalalignment"] = align
        self.propertiesChanged.emit()

    def changeFontSize(self, value: int):
        """ set the font size """
        self.properties["fontsize"] = value
        self.propertiesChanged.emit()

class LegendPropertiesWidget(QtWidgets.QWidget):
    stateChanged = QtCore.Signal(int, str)
    noSignal = False
    target_list = None

    def __init__(self, layout: QtWidgets.QLayout):
        """ A widget that allows to change to properties of a matplotlib legend

        Args:
            layout: the layout to which to add the widget
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        from packaging import version
        import matplotlib as mpl
        ncols_name = "ncols"
        if version.parse(mpl._get_version()) < version.parse("3.6.0"):
            ncols_name = "ncol"

        self.property_names = [
            ("frameon", "frameon", bool, None, None),
            ("borderpad", "borderpad", float, None, "legend_icon_borderpad.png"),
            ("labelspacing", "labelspacing", float, None, "legend_icon_labelspacing.png"),
            ("markerscale", "markerscale", float, None, "legend_icon_markerscale.png"),
            ("handlelength", "handlelength", float, None, "legend_icon_handlelength.png"),
            ("handletextpad", "handletextpad", float, None, "legend_icon_handletextpad.png"),
            (ncols_name, "_" + ncols_name, int, 1, None),
            ("columnspacing", "columnspacing", float, None, "legend_icon_columnspacing.png"),
            ("fontsize", "_fontsize", int, None, "legend_icon_fontsize.png"),
            ("title", "title", str, "", None),
            ("title_fontsize", "title_fontsize", int, None, "legend_icon_title_fontsize.png"),
        ]
        self.properties = {}

        self.widgets = {}
        for index, (name, name2, type_, default_, icon) in enumerate(self.property_names):
            if index % 3 == 0:
                layout = QtWidgets.QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                self.layout.addLayout(layout)
            if type_ == bool:
                widget = CheckWidget(layout, name + ":")
                widget.editingFinished.connect(
                    lambda name=name, widget=widget: self.changePropertiy(name, widget.get()))
            elif type_ == str:
                widget = TextWidget(layout, name + ":")
                widget.editingFinished.connect(
                    lambda name=name, widget=widget: self.changePropertiy(name, widget.get()))
            else:
                label = QtWidgets.QLabel(name + ":")
                layout.addWidget(label)
                if type_ == float:
                    widget = QtWidgets.QDoubleSpinBox()
                    widget.setSingleStep(0.1)
                elif type_ == int:
                    widget = QtWidgets.QSpinBox()
                widget.label = label
                layout.addWidget(widget)
                widget.valueChanged.connect(lambda x, name=name: self.changePropertiy(name, x))

            if icon is not None and getattr(widget, "label", None):
                from pathlib import Path
                pix = QtGui.QPixmap(str(Path(__file__).parent.parent / "icons" / icon))
                pix = pix.scaledToWidth(28*QtGui.QGuiApplication.primaryScreen().logicalDotsPerInch()/96, QtCore.Qt.SmoothTransformation)
                widget.setToolTip(name)
                widget.label.setToolTip(name)
                widget.label.setPixmap(pix)
                widget.label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.widgets[name] = widget

    def changePropertiy(self, name: str, value: Any):
        """ change the property with the given name to the provided value """
        if self.target is None:
            return

        bbox = self.target.get_frame().get_bbox()
        self.properties[name] = value
        axes = self.target.axes
        axes.legend(**self.properties)
        self.target = axes.get_legend()
        fig = self.target.figure
        prop_copy = {}
        for index, (name, name2, type_, default_, icon) in enumerate(self.property_names):
            value = self.properties[name]
            if default_ is not None and value == default_:
                continue
            if default_ is None and value == plt.rcParams["legend." + name]:
                continue
            if type_ == str:
                prop_copy[name] = '"' + value + '"'
            else:
                prop_copy[name] = value
        fig.change_tracker.addChange(axes, ".legend(%s)" % (", ".join("%s=%s" % (k, v) for k, v in prop_copy.items())))
        self.target._set_loc(tuple(self.target.axes.transAxes.inverted().transform(tuple([bbox.x0, bbox.y0]))))
        fig.figure_dragger.make_dragable(self.target)
        fig.figure_dragger.select_element(self.target)
        fig.canvas.draw()
        fig.selection.update_selection_rectangles()
        fig.canvas.draw()

    def setTarget(self, element: Artist):
        """ set the target artist for this widget """
        if isinstance(element, list):
            self.target_list = element
            element = element[0]
        else:
            if element is None:
                self.target_list = []
            else:
                self.target_list = [element]
        self.target = None
        for name, name2, type_, default_, icon in self.property_names:
            if name2 == "frameon":
                value = element.get_frame_on()
            elif name2 == "title":
                value = element.get_title().get_text()
            elif name2 == "title_fontsize":
                value = int(element.get_title().get_fontsize())
            elif name2 == "_fontsize":
                # matplotlib fontsizes are float, but Qt requires int
                value = int(getattr(element, name2))
            else:
                value = getattr(element, name2)

            try:
                self.widgets[name].setValue(value)
            except AttributeError:
                self.widgets[name].set(value)
            self.properties[name] = value

        self.target = element


class QTickEdit(QtWidgets.QWidget):
    def __init__(self, axis: str, signal_target_changed: QtCore.Signal):
        """ A widget to change the tick properties

        Args:
            axis: whether to use the "x" or "y" axis
            signal_target_changed: a signal to emit when the target changed
        """
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("Figure - " + axis + "-Axis - Ticks - Pylustrator")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "../icons", "ticks.ico")))
        self.layout = QtWidgets.QVBoxLayout(self)
        self.axis = axis

        self.label = QtWidgets.QLabel(
            "Ticks can be specified, one tick pre line.\nOptionally a label can be provided, e.g. 1 \"First\",")
        self.layout.addWidget(self.label)

        self.layout2 = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.layout2)

        self.input_ticks = TextWidget(self.layout2, axis + "-Ticks:", multiline=True, horizontal=False)
        self.input_ticks.editingFinished.connect(self.ticksChanged)

        self.input_ticks2 = TextWidget(self.layout2, axis + "-Ticks (minor):", multiline=True, horizontal=False)
        self.input_ticks2.editingFinished.connect(self.ticksChanged2)

        self.input_scale = ComboWidget(self.layout, axis + "-Scale", ["linear", "log", "symlog", "logit"])
        self.input_scale.link(axis + "scale", signal_target_changed)

        self.input_font = TextPropertiesWidget2(self.layout)
        self.input_font.propertiesChanged.connect(self.fontStateChanged)

        self.input_labelpad = NumberWidget(self.layout, axis + "-Labelpad", min=-999)
        self.input_labelpad.link(axis + "axis.labelpad", signal_target_changed, direct=True)

        self.button_ok = QtWidgets.QPushButton("Ok")
        self.layout.addWidget(self.button_ok)
        self.button_ok.clicked.connect(self.hide)

    def parseTickLabel(self, line: str) -> (float, str):
        """ interpret the tick value specified in line """
        import re
        line = line.replace("−", "-")
        match = re.match(r"\$\\mathdefault{(([-.\d]*)\\times)?([-.\d]+)\^{([-.\d]+)}}\$", line)
        if match:
            _, factor, base, exponent = match.groups()
            if factor is not None:
                number = float(factor) * float(base) ** float(exponent)
                line = "%s x %s^%s" % (factor, base, exponent)
            else:
                number = float(base) ** float(exponent)
                line = "%s^%s" % (base, exponent)
        else:
            try:
                number = float(line)
            except ValueError:
                number = np.nan
        return number, line

    def formatTickLabel(self, line: str) -> (float, str):
        """ interpret the tick label specified in line"""
        import re
        line = line.replace("−", "-")
        match = re.match(r"\s*(([-.\d]*)\s*x)?\s*([-.\d]+)\s*\^\s*([-.\d]+)\s*\"(.+)?\"", line)
        match2 = re.match(r"\s*(([-.\d]*)\s*x)?\s*([-.\d]+)\s*\^\s*([-.\d]+)\s*(.+)?", line)
        if match:
            _, factor, base, exponent, label = match.groups()
            if factor is not None:
                number = float(factor) * float(base) ** float(exponent)
                line = r"$\mathdefault{%s\times%s^{%s}}$" % (factor, base, exponent)
            else:
                number = float(base) ** float(exponent)
                line = r"$\mathdefault{%s^{%s}}$" % (base, exponent)
            if label is not None:
                line = label
        elif match2:
            _, factor, base, exponent, label = match2.groups()
            if factor is not None:
                number = float(factor) * float(base) ** float(exponent)
                line = r"$\mathdefault{%s\times%s^{%s}}$" % (factor, base, exponent)
            else:
                number = float(base) ** float(exponent)
                line = r"$\mathdefault{%s^{%s}}$" % (base, exponent)
            if label is not None:
                line = label
        else:
            try:
                number = float(line)
            except ValueError:
                number = np.nan
        return number, line

    def setTarget(self, element: Artist):
        """ set the target Artist for this widget"""
        self.element = element
        self.fig = element.figure
        min, max = getattr(self.element, "get_" + self.axis + "lim")()
        self.range = [min, max]

        ticks = getattr(self.element, "get_" + self.axis + "ticks")()
        labels = getattr(self.element, "get_" + self.axis + "ticklabels")()
        text = []
        for t, l in zip(ticks, labels):
            l, l_text = self.parseTickLabel(l.get_text())
            try:
                l = float(l)
            except ValueError:
                continue
            if min <= t <= max:
                if l != t:
                    text.append("%s \"%s\"" % (str(t), l_text))
                else:
                    text.append("%s" % l_text)
        self.input_ticks.setText(",<br>".join(text))

        ticks = getattr(self.element, "get_" + self.axis + "ticks")(minor=True)
        labels = getattr(self.element, "get_" + self.axis + "ticklabels")(minor=True)
        text = []
        for t, l in zip(ticks, labels):
            l, l_text = self.parseTickLabel(l.get_text())
            try:
                l = float(l)
            except ValueError:
                pass
            if min <= t <= max:
                if l != t:
                    text.append("%s \"%s\"" % (str(t), l_text))
                else:
                    text.append("%s" % l_text)
        self.input_ticks2.setText(",<br>".join(text))

        elements = [self.element]
        elements += [element.target for element in self.element.figure.selection.targets if
                     element.target != self.element and isinstance(element.target, Axes)]
        ticks = []
        for element in elements:
            ticks += [t.label1 for t in getattr(element, "get_" + self.axis + "axis")().get_major_ticks()]

        self.input_font.setTarget(ticks)

    def parseTicks(self, string: str):
        """ parse a list of given ticks """
        try:
            ticks = []
            labels = []
            for line in string.split("\n"):
                line = line.strip().strip(",")
                two_parts = line.split(" ", 1)
                try:
                    tick, _ = self.formatTickLabel(line)
                    if np.isnan(tick) and len(two_parts) == 2:
                        tick = float(two_parts[0].replace("−", "-"))
                        label = two_parts[1].strip("\"")
                    else:
                        tick, label = self.formatTickLabel(line)
                except ValueError as err:
                    pass
                else:
                    if not np.isnan(tick):
                        ticks.append(tick)
                        labels.append(label)
        except Exception as err:
            pass
        return ticks, labels

    def str(self, object: Any):
        """ serialize an object and interpret nan values """
        if str(object) == "nan":
            return "np.nan"
        return str(object)

    def ticksChanged2(self):
        """ when the minor ticks changed """
        ticks, labels = self.parseTicks(self.input_ticks2.text())

        elements = [self.element]
        elements += [element.target for element in self.element.figure.selection.targets if
                     element.target != self.element and isinstance(element.target, Axes)]

        for element in elements:
            getattr(element, "set_" + self.axis + "lim")(self.range)
            getattr(element, "set_" + self.axis + "ticks")(ticks, minor=True)
            getattr(element, "set_" + self.axis + "ticklabels")(labels, minor=True)
            min, max = getattr(element, "get_" + self.axis + "lim")()
            if min != self.range[0] or max != self.range[1]:
                self.fig.change_tracker.addChange(element,
                                                  ".set_" + self.axis + "lim(%s, %s)" % (str(min), str(max)))
            else:
                self.fig.change_tracker.addChange(element,
                                                  ".set_" + self.axis + "lim(%s, %s)" % (
                                                  str(self.range[0]), str(self.range[1])))

            # self.setTarget(element)
            self.fig.change_tracker.addChange(element,
                                              ".set_" + self.axis + "ticks([%s], minor=True)" % ", ".join(
                                                  self.str(t) for t in ticks), element,
                                              ".set_" + self.axis + "ticks_minor")
            self.fig.change_tracker.addChange(element, ".set_" + self.axis + "ticklabels([%s], minor=True)" % ", ".join(
                '"' + l + '"' for l in labels), element, ".set_" + self.axis + "labels_minor")
        self.fig.canvas.draw()

    def getFontProperties(self):
        prop_copy = {}
        prop_copy2 = {}
        for index, (name, name2, type_, default_) in enumerate(self.input_font.property_names):
            if name not in self.input_font.properties:
                continue
            value = self.input_font.properties[name]
            if default_ is not None and value == default_:
                continue
            #if default_ is None and value == plt.rcParams["legend." + name]:
            #    continue
            if type_ == str:
                prop_copy[name] = '"' + value + '"'
            else:
                prop_copy[name] = value
            prop_copy2[name] = value
        return (", ".join("%s=%s" % (k, v) for k, v in prop_copy.items())), prop_copy2

    def fontStateChanged(self):
        self.ticksChanged()
        #fig.change_tracker.addChange(axes, ".legend(%s)" % (", ".join("%s=%s" % (k, v) for k, v in prop_copy.items())))


    def ticksChanged(self):
        """ when the major ticks changed """
        ticks, labels = self.parseTicks(self.input_ticks.text())

        elements = [self.element]
        elements += [element.target for element in self.element.figure.selection.targets if
                     element.target != self.element and isinstance(element.target, Axes)]

        for element in elements:
            getattr(element, "set_" + self.axis + "lim")(self.range)
            getattr(element, "set_" + self.axis + "ticks")(ticks)
            getattr(element, "set_" + self.axis + "ticklabels")(labels, **self.getFontProperties()[1])
            min, max = getattr(element, "get_" + self.axis + "lim")()
            if min != self.range[0] or max != self.range[1]:
                self.fig.change_tracker.addChange(element,
                                                  ".set_" + self.axis + "lim(%s, %s)" % (str(min), str(max)))
            else:
                self.fig.change_tracker.addChange(element,
                                                  ".set_" + self.axis + "lim(%s, %s)" % (
                                                  str(self.range[0]), str(self.range[1])))

            # self.setTarget(self.element)
            self.fig.change_tracker.addChange(element, ".set_" + self.axis + "ticks([%s])" % ", ".join(
                self.str(t) for t in ticks))
            self.fig.change_tracker.addChange(element, ".set_" + self.axis + "ticklabels([%s], %s)" % (", ".join(
                '"' + l + '"' for l in labels), self.getFontProperties()[0]))
        self.fig.canvas.draw()


class QAxesProperties(QtWidgets.QWidget):
    targetChanged_wrapped = QtCore.Signal(object)

    def __init__(self, layout: QtWidgets.QLayout, axis: str, signal_target_changed: QtCore.Signal):
        """ a widget to change the properties of an axes (label, limits)

        Args:
            layout: the layout to which to add this widget
            axis: whether to use "x" or the "y" axis
            signal_target_changed: the signal when a target changed
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.targetChanged = signal_target_changed
        self.targetChanged.connect(self.setTarget)

        self.input_label = TextWidget(self.layout, axis + "-Label:")

        def wrapTargetLabel(axis_object):
            try:
                target = getattr(getattr(axis_object, f"get_{axis}axis")(), "get_label")()
            except AttributeError:
                target = None
            self.targetChanged_wrapped.emit(target)

        self.targetChanged.connect(wrapTargetLabel)
        self.input_label.link("text", signal=self.targetChanged_wrapped)

        self.input_lim = DimensionsWidget(self.layout, axis + "-Lim:", "-", "", free=True)
        self.input_lim.link(axis + "lim", signal=self.targetChanged)
        if axis == "x":
            self.button_ticks = QtWidgets.QPushButton(
                QtGui.QIcon(os.path.join(os.path.dirname(__file__), "../icons", "ticks.ico")), "")
        else:
            self.button_ticks = QtWidgets.QPushButton(
                QtGui.QIcon(os.path.join(os.path.dirname(__file__), "../icons", "ticks_y.ico")), "")
        self.button_ticks.clicked.connect(self.showTickWidget)
        self.layout.addWidget(self.button_ticks)

        self.tick_edit = QTickEdit(axis, signal_target_changed)

    def showTickWidget(self):
        """ open the tick edit dialog """
        self.tick_edit.setTarget(self.element)
        self.tick_edit.show()

    def setTarget(self, element: Artist):
        """ set the target Artist of this widget """
        self.element = element

        if isinstance(element, Axes):
            self.show()
        else:
            self.hide()




class QItemProperties(QtWidgets.QWidget):
    targetChanged = QtCore.Signal(object)
    valueChanged = QtCore.Signal(tuple)
    element = None

    def __init__(self, layout: QtWidgets.QLayout, signals: "Signals"):
        """ a widget that holds all the properties to set and the tree view

        Args:
            layout: the layout to which to add the widget
            fig: the figure
            tree: the tree view of the elements of the figure
            parent: the parent widget
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.signals = signals

        signals.figure_changed.connect(self.setFigure)
        signals.figure_element_selected.connect(self.select_element)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.label = QtWidgets.QLabel()
        self.layout.addWidget(self.label)

        self.input_text = TextWidget(self.layout, "Text:")
        self.input_text.link("text", self.targetChanged)

        self.input_rotation = NumberWidget(self.layout, "Rotation:")
        self.input_rotation.link("rotation", self.targetChanged)
        self.input_rotation.input1.setRange(-360, 360)

        self.input_xaxis = QAxesProperties(self.layout, "x", self.targetChanged)
        self.input_yaxis = QAxesProperties(self.layout, "y", self.targetChanged)

        self.input_font_properties = TextPropertiesWidget(self.layout)

        self.input_legend_properties = LegendPropertiesWidget(self.layout)

        self.input_label = TextWidget(self.layout, "Label:")
        self.input_label.link("label", self.targetChanged)

        layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(layout)

        condition_line = lambda x: getattr(x, "get_linestyle")() not in ["None", " ", ""]
        condition_marker = lambda x: getattr(x, "get_marker")() not in ["None", " ", ""]

        TextWidget(layout, "Linestyle:").link("linestyle", self.targetChanged)

        NumberWidget(layout, "Linewidth:").link("linewidth", self.targetChanged,
                                                condition=condition_line)  # lambda x: getattr(x, "get_linestyle") not in ["None", " ", ""])

        QColorWidget(layout, "Color:").link("color", self.targetChanged, condition=condition_line)

        layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(layout)

        TextWidget(layout, "Markerstyle:").link("marker", self.targetChanged)

        NumberWidget(layout, "Markersize:").link("markersize", self.targetChanged, condition=condition_marker)

        QColorWidget(layout, "markerfacecolor:").link("markerfacecolor", self.targetChanged, condition=condition_marker)

        layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(layout)

        NumberWidget(layout, "Markeredgewidth:").link("markeredgewidth", self.targetChanged, condition=condition_marker)

        QColorWidget(layout, "markeredgecolor:").link("markeredgecolor", self.targetChanged, condition=condition_marker)

        layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(layout)

        QColorWidget(layout, "Edgecolor:").link("edgecolor", self.targetChanged)

        QColorWidget(layout, "Facecolor:").link("facecolor", self.targetChanged)

        self.layout_buttons = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.layout_buttons)

        self.button_add_image = QtWidgets.QPushButton("add image")
        self.layout_buttons.addWidget(self.button_add_image)
        self.button_add_image.clicked.connect(self.buttonAddImageClicked)

        self.button_add_text = QtWidgets.QPushButton("add text")
        self.layout_buttons.addWidget(self.button_add_text)
        self.button_add_text.clicked.connect(self.buttonAddTextClicked)

        self.button_add_annotation = QtWidgets.QPushButton("add annotation")
        self.layout_buttons.addWidget(self.button_add_annotation)
        self.button_add_annotation.clicked.connect(self.buttonAddAnnotationClicked)
        self.layout_buttons = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.layout_buttons)

        self.button_add_rectangle = QtWidgets.QPushButton("add rectangle")
        self.layout_buttons.addWidget(self.button_add_rectangle)
        self.button_add_rectangle.clicked.connect(self.buttonAddRectangleClicked)

        self.button_add_arrow = QtWidgets.QPushButton("add arrow")
        self.layout_buttons.addWidget(self.button_add_arrow)
        self.button_add_arrow.clicked.connect(self.buttonAddArrowClicked)

        self.layout_buttons = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.layout_buttons)

        self.button_despine = QtWidgets.QPushButton("despine")
        self.layout_buttons.addWidget(self.button_despine)
        self.button_despine.clicked.connect(self.buttonDespineClicked)

        self.button_grid = QtWidgets.QPushButton("grid")
        self.layout_buttons.addWidget(self.button_grid)
        self.button_grid.clicked.connect(self.buttonGridClicked)

        self.button_legend = QtWidgets.QPushButton("legend")
        self.layout_buttons.addWidget(self.button_legend)
        self.button_legend.clicked.connect(self.buttonLegendClicked)

        self.setElement(None)
        self.setMinimumWidth(100)

    def select_element(self, element: Artist):
        """ select an element """
        if element is None:
            self.setElement(self.fig)
        else:
            self.setElement(element)

    def setFigure(self, fig):
        self.fig = fig

    def buttonAddImageClicked(self):
        """ when the button 'add image' is clicked """
        fig = self.fig

        def addChange(element, command):
            fig.change_tracker.addChange(element, command)
            return eval(getReference(element) + command)

        path = QtWidgets.QFileDialog.getOpenFileName(self, "Open Image", os.getcwd(),
                                                     "Image *.jpg *.png *.tif")
        if isinstance(path, tuple):
            path = str(path[0])
        else:
            path = str(path)
        if not path:
            return
        filename = path
        if isinstance(self.element, Figure):
            axes = self.element.add_axes([0.25, 0.25, 0.5, 0.5], label=filename)
            fig.ax_dict = {ax.get_label(): ax for ax in fig.axes}
            self.fig.change_tracker.addChange(self.element,
                                              ".add_axes([0.25, 0.25, 0.5, 0.5], label=\"%s\")  # id=%s.new" % (
                                                  filename, getReference(axes)), axes, ".new")
        addChange(axes, ".imshow(plt.imread(\"%s\"))" % filename)
        addChange(axes, '.set_xticks([])')
        addChange(axes, '.set_yticks([])')
        if 0:
            addChange(axes, ".spines['right'].set_visible(False)")
            addChange(axes, ".spines['left'].set_visible(False)")
            addChange(axes, ".spines['top'].set_visible(False)")
            addChange(axes, ".spines['bottom'].set_visible(False)")
        else:
            addChange(axes, ".spines[:].set_visible(False)")

        self.signals.figure_element_child_created.emit(self.element)
        self.fig.figure_dragger.make_dragable(axes)
        self.fig.figure_dragger.select_element(axes)
        self.fig.canvas.draw()
        self.setElement(axes)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddTextClicked(self):
        """ when the button 'add text' is clicked """
        if isinstance(self.element, Axes):
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transAxes)
            self.fig.change_tracker.addChange(self.element,
                                              ".text(0.5, 0.5, 'New Text', transform=%s.transAxes)  # id=%s.new" % (
                                                  getReference(self.element), getReference(text)), text, ".new")
            text.is_new_text = True
        if isinstance(self.element, Figure):
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transFigure)
            self.fig.change_tracker.addChange(self.element,
                                              ".text(0.5, 0.5, 'New Text', transform=%s.transFigure)  # id=%s.new" % (
                                                  getReference(self.element), getReference(text)), text, ".new")
            text.is_new_text = True
        self.signals.figure_element_child_created.emit(self.element)
        self.fig.figure_dragger.make_dragable(text)
        self.fig.canvas.draw()
        self.fig.figure_dragger.on_deselect(None)
        self.fig.figure_dragger.selection.clear_targets()
        if isinstance(self.element, Axes):
            self.fig.figure_dragger.select_element(text)
        self.setElement(text)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddAnnotationClicked(self):
        """ when the button 'add annoations' is clicked """
        text = self.element.annotate("New Annotation", (self.element.get_xlim()[0], self.element.get_ylim()[0]),
                                     (np.mean(self.element.get_xlim()), np.mean(self.element.get_ylim())),
                                     arrowprops=dict(arrowstyle="->"))
        self.fig.change_tracker.addChange(self.element,
                                          ".annotate('New Annotation', %s, %s, arrowprops=dict(arrowstyle='->'))  # id=%s.new" % (
                                          text.xy, text.get_position(), getReference(text)),
                                          text, ".new")

        self.signals.figure_element_child_created.emit(self.element)
        self.fig.figure_dragger.make_dragable(text)
        self.fig.figure_dragger.select_element(text)
        self.fig.canvas.draw()
        self.setElement(text)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddRectangleClicked(self):
        """ when the button 'add rectangle' is clicked """
        p = mpl.patches.Rectangle((self.element.get_xlim()[0], self.element.get_ylim()[0]),
                                  width=np.mean(self.element.get_xlim()), height=np.mean(self.element.get_ylim()), )
        self.element.add_patch(p)

        self.fig.change_tracker.addChange(self.element,
                                          ".add_patch(mpl.patches.Rectangle(%s, width=%s, height=%s))  # id=%s.new" % (
                                              p.get_xy(), p.get_width(), p.get_height(), getReference(p)),
                                          p, ".new")

        self.signals.figure_element_child_created.emit(self.element)
        self.fig.figure_dragger.make_dragable(p)
        self.fig.figure_dragger.select_element(p)
        self.fig.canvas.draw()
        self.setElement(p)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddArrowClicked(self):
        """ when the button 'add arrow' is clicked """
        p = mpl.patches.FancyArrowPatch((self.element.get_xlim()[0], self.element.get_ylim()[0]),
                                        (np.mean(self.element.get_xlim()), np.mean(self.element.get_ylim())),
                                        arrowstyle="Simple,head_length=10,head_width=10,tail_width=2",
                                        facecolor="black", clip_on=False, zorder=2)
        self.element.add_patch(p)

        self.fig.change_tracker.addChange(self.element,
                                          ".add_patch(mpl.patches.FancyArrowPatch(%s, %s, arrowstyle='Simple,head_length=10,head_width=10,tail_width=2', facecolor='black', clip_on=False, zorder=2))  # id=%s.new" % (
                                          p._posA_posB[0], p._posA_posB[1], getReference(p)),
                                          p, ".new")

        self.signals.figure_element_child_created.emit(self.element)
        self.fig.figure_dragger.make_dragable(p)
        self.fig.figure_dragger.select_element(p)
        self.fig.canvas.draw()
        self.setElement(p)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonDespineClicked(self):
        """ despine the target """

        if version.parse(mpl.__version__) < version.parse("3.4.0"):
            commands = [".spines['right'].set_visible(False)", ".spines['top'].set_visible(False)"]
        else:
            commands = [".spines[['right', 'top']].set_visible(False)"]
        for command in commands:
            elements = [element.target for element in self.element.figure.selection.targets
                        if isinstance(element.target, Axes)]
            for element in elements:
                eval("element" + command)
                self.fig.change_tracker.addChange(element, command)
        self.fig.canvas.draw()

    def buttonGridClicked(self):
        """ toggle the grid of the target """
        elements = [element.target for element in self.element.figure.selection.targets
                    if isinstance(element.target, Axes)]

        def set_false():
            for element in elements:
                element.grid(False)
                self.fig.change_tracker.addChange(element, ".grid(False)")
        def set_true():
            for element in elements:
                element.grid(True)
                self.fig.change_tracker.addChange(element, ".grid(True)")

        if getattr(self.element.xaxis, "_gridOnMajor", False) or getattr(self.element.xaxis, "_major_tick_kw", {"gridOn": False})['gridOn']:
            set_false()
            self.fig.change_tracker.addEdit([set_true, set_false, "Grid off"])
        else:
            set_true()
            self.fig.change_tracker.addEdit([set_false, set_true, "Grid on"])
        self.fig.canvas.draw()

    def buttonLegendClicked(self):
        """ add a legend to the target """
        self.element.legend()
        self.fig.change_tracker.addChange(self.element, ".legend()")
        self.fig.figure_dragger.make_dragable(self.element.get_legend())
        self.fig.canvas.draw()
        self.signals.figure_element_child_created.emit(self.element)

    def changePickable(self):
        """ make the target pickable """
        if self.input_picker.isChecked():
            self.element._draggable.connect()
        else:
            self.element._draggable.disconnect()
        self.signals.figure_element_child_created.emit(self.element)

    def setElement(self, element: Artist):
        """ set the target Artist of this widget """
        self.label.setText(str(element))
        self.element = element
        try:
            element._draggable
        except AttributeError:
            pass

        self.button_add_annotation.hide()
        self.button_add_rectangle.hide()
        self.button_despine.hide()
        self.button_grid.hide()
        self.button_add_image.hide()
        self.button_add_arrow.hide()
        self.button_legend.hide()
        if isinstance(element, Figure):
            self.button_add_text.show()
            self.button_add_image.show()
        elif isinstance(element, Axes):
            self.button_add_text.show()
            self.button_add_annotation.show()
            self.button_despine.show()
            self.button_grid.show()
            self.button_add_arrow.show()
            self.button_add_rectangle.show()
            self.button_legend.show()
        else:
            self.button_add_text.hide()

        if isinstance(element, mpl.legend.Legend):
            self.input_legend_properties.show()
            self.input_legend_properties.setTarget(element)
        else:
            self.input_legend_properties.hide()

        try:
            self.input_font_properties.show()
            elements = [element]
            elements += [element.target for element in element.figure.selection.targets if
                         element.target != element]
            self.input_font_properties.setTarget(elements)
        except AttributeError:
            self.input_font_properties.hide()

        self.targetChanged.emit(element)

