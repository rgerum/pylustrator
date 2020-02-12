import os
import sys
import traceback

import qtawesome as qta
from matplotlib import _pylab_helpers

from .QComplexWidgets import *
from .ax_rasterisation import rasterizeAxes, restoreAxes
from .change_tracker import setFigureVariableNames
from .drag_helper import DragManager
from .exception_swallower import swallow_get_exceptions
from .matplotlibwidget import MatplotlibWidget

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from qtpy import QtCore, QtWidgets, QtGui


class Linkable:
    """ a class that automatically links a widget with the property of a matplotlib artist
    """

    def link(self, property_name: str, signal: QtCore.Signal = None, condition: callable = None, direct: bool = False):
        self.element = None
        self.direct = direct
        if direct:
            parts = property_name.split(".")
            s = self
            def get():
                target = s.element
                for part in parts:
                    target = getattr(target, part)
                return target
            def set(v):
                get()
                target = s.element
                for part in parts[:-1]:
                    target = getattr(target, part)
                setattr(target, parts[-1], v)
                return [s.element]
            self.setLinkedProperty = set
            self.getLinkedProperty = get
            self.serializeLinkedProperty = lambda x: "." + property_name + " = %s" % x
        else:
            def set(v):
                elements = []
                getattr(self.element, "set_" + property_name)(v)
                elements.append(self.element)
                for elm in self.element.figure.selection.targets:
                    elm = elm.target
                    if elm != self.element:
                        try:
                            getattr(elm, "set_"+property_name, None)(v)
                        except TypeError as err:
                            pass
                        else:
                            elements.append(elm)
                return elements
            self.setLinkedProperty = set#lambda text: getattr(self.element, "set_"+property_name)(text)
            self.getLinkedProperty = lambda: getattr(self.element, "get_"+property_name)()
            self.serializeLinkedProperty = lambda x: ".set_"+property_name+"(%s)" % x

        if condition is None:
            self.condition = lambda x: True
        else:
            self.condition = condition

        self.editingFinished.connect(self.updateLink)
        signal.connect(self.setTarget)

    def setTarget(self, element: Artist):
        """ set the target for the widget """
        self.element = element
        try:
            self.set(self.getLinkedProperty())
            self.setEnabled(self.condition(element))
        except AttributeError:
            self.hide()
        else:
            self.show()

    def updateLink(self):
        """ update the linked property """
        try:
            elements = self.setLinkedProperty(self.get())
        except AttributeError:
            return
        for element in elements:
            if isinstance(element, mpl.figure.Figure):
                fig = element
            else:
                fig = element.figure
            fig.change_tracker.addChange(element, self.serializeLinkedProperty(self.getSerialized()))
        fig.canvas.draw()

    def set(self, value):
        """ set the value (to be overloaded) """
        pass

    def get(self):
        """ get the value """
        return None

    def getSerialized(self):
        """ serialize the value for saving as a command """
        return ""


class FreeNumberInput(QtWidgets.QLineEdit):
    """ like a QSpinBox for number import, but without min or max range or a fixed resolution.
    Especially important for the limits of logarithmic plots.
    """
    send_signal = True
    valueChanged = QtCore.Signal(float)

    def __init__(self):
        QtWidgets.QLineEdit.__init__(self)
        self.textChanged.connect(self.emitValueChanged)

    def emitValueChanged(self, value):
        if self.send_signal:
            try:
                value = self.value()
                self.valueChanged.emit(value)
                self.setStyleSheet("")
            except TypeError:
                self.setStyleSheet("background: #d56060; border: red")
                pass

    def value(self):
        try:
            return float(self.text())
        except ValueError:
            try:
                return float(self.text().replace(",", "."))
            except ValueError:
                return None

    def setValue(self, value):
        self.send_signal = False
        try:
            self.setText(str(value))
            self.setCursorPosition(0)
        finally:
            self.send_signal = True


class DimensionsWidget(QtWidgets.QWidget, Linkable):
    """ a widget that lets the user input a pair of dimensions (e.g. widh and height)
    """
    valueChanged = QtCore.Signal(tuple)
    transform = None
    noSignal = False

    def __init__(self, layout: QtWidgets.QLayout, text: str, join: str, unit: str, free: bool = False):
        """
        :param layout: the layout to which to add the widget
        :param text: the label of the widget
        :param join: a text between the two parts
        :param unit: a unit for the values
        :param free: whether to use free number input widgets instead of QSpinBox
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.text = QtWidgets.QLabel(text)
        self.layout.addWidget(self.text)
        self.layout.setContentsMargins(0, 0, 0, 0)

        if free:
            self.input1 = FreeNumberInput()
        else:
            self.input1 = QtWidgets.QDoubleSpinBox()
            self.input1.setSuffix(" "+unit)
            self.input1.setSingleStep(0.1)
            self.input1.setMaximum(99999)
            self.input1.setMinimum(-99999)
        self.input1.valueChanged.connect(self.onValueChanged)
        self.layout.addWidget(self.input1)

        self.text2 = QtWidgets.QLabel(join)
        self.text2.setMaximumWidth(self.text2.fontMetrics().width(join))
        self.layout.addWidget(self.text2)

        if free:
            self.input2 = FreeNumberInput()
        else:
            self.input2 = QtWidgets.QDoubleSpinBox()
            self.input2.setSuffix(" "+unit)
            self.input2.setSingleStep(0.1)
            self.input2.setMaximum(99999)
            self.input2.setMinimum(-99999)
        self.input2.valueChanged.connect(self.onValueChanged)
        self.layout.addWidget(self.input2)

        self.editingFinished = self.valueChanged

    def setText(self, text: str):
        """
        :param text: The test to set.
        :return:
        """
        self.text.setText(text)

    def setUnit(self, unit: str):
        """
        Sets the text for the unit for the values
        :param unit: the unit text to set
        :return:
        """
        self.input1.setSuffix(" "+unit)
        self.input2.setSuffix(" "+unit)

    def setTransform(self, transform: mpl.transforms.Transform):
        """
        :param transform: the transform which is applied to the values
        :return:
        """
        self.transform = transform

    def onValueChanged(self, value):
        """ called when the value was changed -> emit the value changed signal
        """
        if not self.noSignal:
            self.valueChanged.emit(tuple(self.value()))

    def setValue(self, values: tuple):
        """
        :param values: the two values to set
        :return:
        """
        self.noSignal = True
        if self.transform:
            values = self.transform.transform(values)
        self.input1.setValue(values[0])
        self.input2.setValue(values[1])
        self.noSignal = False

    def value(self):
        """ get the value """
        tuple = (self.input1.value(), self.input2.value())
        if self.transform:
            tuple = self.transform.inverted().transform(tuple)
        return tuple

    def get(self) -> tuple:
        """
        :return: get the value
        """
        return self.value()

    def set(self, value: tuple):
        """
        :param value: the value to set
        :return:
        """
        self.setValue(value)

    def getSerialized(self) -> str:
        """ serialize the values """
        return ", ".join([str(i) for i in self.get()])


class TextWidget(QtWidgets.QWidget, Linkable):
    """ a text input widget with a label. """
    editingFinished = QtCore.Signal()
    noSignal = False
    last_text = None

    def __init__(self, layout: QtWidgets.QLayout, text: str, multiline: bool = False, horizontal: bool = True):
        """
        :param layout: the layout to which to add the widget
        :param text: the label text
        :param multiline: whether the text input should be a single line or not
        :param horizontal: whether the layout should be left or above the input
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        if horizontal:
            self.layout = QtWidgets.QHBoxLayout(self)
        else:
            self.layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.multiline = multiline
        if multiline:
            self.input1 = QtWidgets.QTextEdit()
            self.input1.textChanged.connect(self.valueChangeEvent)
            self.input1.text = self.input1.toPlainText
        else:
            self.input1 = QtWidgets.QLineEdit()
            self.input1.editingFinished.connect(self.valueChangeEvent)
        self.layout.addWidget(self.input1)

    def valueChangeEvent(self):
        if not self.noSignal and self.input1.text() != self.last_text:
            self.editingFinished.emit()

    def setLabel(self, text: str):
        self.label.setLabel(text)

    def setText(self, text: str):
        self.noSignal = True
        text = text.replace("\n", "\\n")
        self.last_text = text
        if self.multiline:
            self.input1.setText(text)
        else:
            self.input1.setText(text)
        self.noSignal = False

    def text(self) -> str:
        text = self.input1.text()
        return text.replace("\\n", "\n")

    def get(self) -> str:
        return self.text()

    def set(self, value: str):
        self.setText(value)

    def getSerialized(self) -> str:
        return "\""+str(self.get())+"\""


class NumberWidget(QtWidgets.QWidget, Linkable):
    editingFinished = QtCore.Signal()
    noSignal = False

    def __init__(self, layout, text, min=None, use_float=True):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.type = float if use_float else int
        if use_float is False:
            self.input1 = QtWidgets.QSpinBox()
        else:
            self.input1 = QtWidgets.QDoubleSpinBox()
        if min is not None:
            self.input1.setMinimum(min)
        self.input1.valueChanged.connect(self.valueChangeEvent)
        self.layout.addWidget(self.input1)

    def valueChangeEvent(self):
        if not self.noSignal:
            self.editingFinished.emit()

    def setLabel(self, text):
        self.label.setLabel(text)

    def setValue(self, text):
        self.noSignal = True
        self.input1.setValue(text)
        self.noSignal = False

    def value(self):
        text = self.input1.value()
        return text

    def get(self):
        return self.value()

    def set(self, value):
        self.setValue(value)

    def getSerialized(self):
        return self.get()


class ComboWidget(QtWidgets.QWidget, Linkable):
    editingFinished = QtCore.Signal()
    noSignal = False

    def __init__(self, layout, text, values):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.values = values

        self.input1 = QtWidgets.QComboBox()
        self.input1.addItems(values)
        self.layout.addWidget(self.input1)

        self.input1.currentIndexChanged.connect(self.valueChangeEvent)
        self.layout.addWidget(self.input1)

    def valueChangeEvent(self):
        if not self.noSignal:
            self.editingFinished.emit()

    def setLabel(self, text):
        self.label.setLabel(text)

    def setText(self, text):
        self.noSignal = True
        index = self.values.index(text)
        self.input1.setCurrentIndex(index)
        self.noSignal = False

    def text(self):
        index = self.input1.currentIndex()
        return self.values[index]

    def get(self):
        return self.text()

    def set(self, value):
        self.setText(value)

    def getSerialized(self):
        return "\""+str(self.get())+"\""


class CheckWidget(QtWidgets.QWidget, Linkable):
    """ a Widget that contains a checkbox and a label """
    editingFinished = QtCore.Signal()
    stateChanged = QtCore.Signal(int)
    noSignal = False

    def __init__(self, layout: QtWidgets.QLabel, text: str):
        """
        :param layout: the layout to which to add the widget
        :param text: the label text
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.input1 = QtWidgets.QCheckBox()
        self.input1.setTristate(False)
        self.input1.stateChanged.connect(self.onStateChanged)
        self.layout.addWidget(self.input1)

    def onStateChanged(self):
        if not self.noSignal:
            self.stateChanged.emit(self.input1.isChecked())
            self.editingFinished.emit()

    def setChecked(self, state: bool):
        self.noSignal = True
        self.input1.setChecked(state)
        self.noSignal = False

    def isChecked(self) -> bool:
        return self.input1.isChecked()

    def get(self) -> bool:
        return self.isChecked()

    def set(self, value: bool):
        self.setChecked(value)

    def getSerialized(self) -> str:
        return "True" if self.get() else "False"


class RadioWidget(QtWidgets.QWidget):
    stateChanged = QtCore.Signal(int, str)
    noSignal = False

    def __init__(self, layout, texts):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.radio_buttons = []

        self.texts = texts

        for name in texts:
            radio = QtWidgets.QRadioButton(name)
            radio.toggled.connect(self.onToggled)
            self.layout.addWidget(radio)
            self.radio_buttons.append(radio)
        self.radio_buttons[0].setChecked(True)

    def onToggled(self, checked):
        if checked:
            self.checked = np.argmax([radio.isChecked() for radio in self.radio_buttons])
            if not self.noSignal:
                self.stateChanged.emit(self.checked, self.texts[self.checked])

    def setState(self, state):
        self.noSignal = True
        for index, radio in enumerate(self.radio_buttons):
            radio.setChecked(state == index)
        self.checked = state
        self.noSignal = False

    def getState(self):
        return self.checked



class QColorWidget(QtWidgets.QWidget, Linkable):
    valueChanged = QtCore.Signal(str)

    def __init__(self, layout, text=None, value=None):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self)

        if text is not None:
            self.label = QtWidgets.QLabel(text)
            self.layout.addWidget(self.label)

        self.button = QtWidgets.QPushButton()
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.OpenDialog)
        # default value for the color
        if value is None:
            value = "#FF0000FF"
        # set the color
        self.setColor(value)

        self.editingFinished = self.valueChanged

    def changeEvent(self, event):
        if event.type() == QtCore.QEvent.EnabledChange:
            if not self.isEnabled():
                self.button.setStyleSheet("background-color: #f0f0f0;")
            else:
                self.setColor(self.color)

    def OpenDialog(self):
        # get new color from color picker
        self.current_color = QtGui.QColor(*tuple(mpl.colors.to_rgba_array(self.getColor())[0]*255))
        self.dialog = QtWidgets.QColorDialog(self.current_color, self.parent())
        self.dialog.setOptions(QtWidgets.QColorDialog.ShowAlphaChannel)
        for index, color in enumerate(plt.rcParams['axes.prop_cycle'].by_key()['color']):
            self.dialog.setCustomColor(index, QtGui.QColor(color))
        self.dialog.open(self.dialog_finished)
        self.dialog.currentColorChanged.connect(self.dialog_changed)
        self.dialog.rejected.connect(self.dialog_rejected)

    def dialog_rejected(self):
        color = self.current_color
        color = color.name()+"%0.2x" % color.alpha()
        self.setColor(color)
        self.valueChanged.emit(self.color)

    def dialog_changed(self):
        color = self.dialog.currentColor()
        # if a color is set, apply it
        if color.isValid():
            color = color.name()+"%0.2x" % color.alpha()
            self.setColor(color)
            self.valueChanged.emit(self.color)

    def dialog_finished(self):
        color = self.dialog.selectedColor()
        self.dialog = None
        # if a color is set, apply it
        if color.isValid():
            color = color.name()+"%0.2x" % color.alpha()
            self.setColor(color)
            self.valueChanged.emit(self.color)

    def setColor(self, value):
        # display and save the new color
        if value is None:
            value = "#FF0000FF"
        self.button.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        if len(value) == 9:
            self.button.setStyleSheet("background-color: rgba(%d, %d, %d, %d%%);" % (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16), int(value[7:], 16)*100/255))
        else:
            self.button.setStyleSheet("background-color: %s;" % (value,))
        self.color = value

    def getColor(self):
        # return the color
        return self.color

    def get(self):
        return self.getColor()

    def set(self, value):
        try:
            if len(value) == 4:
                self.setColor(mpl.colors.to_hex(value) + "%02X" % int(value[-1]*255))
            else:
                self.setColor(mpl.colors.to_hex(value))
        except ValueError:
            self.setColor(None)

    def getSerialized(self):
        return "\""+self.color+"\""

