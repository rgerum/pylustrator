from __future__ import division, print_function
from qtpy import QtCore, QtWidgets, QtGui

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from .matplotlibwidget import MatplotlibWidget
from matplotlib import _pylab_helpers
import matplotlib as mpl
import qtawesome as qta
from matplotlib.figure import Figure
from matplotlib.axes._subplots import Axes
import matplotlib.transforms as transforms

from .drag_bib import FigureDragger
from .helper_functions import changeFigureSize
from .drag_bib import getReference

from .drag_helper import DragManager

import sys


def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook

""" Matplotlib overlaod """
figures = {}
app = None
keys_for_lines = {}


def initialize():
    global app, keys_for_lines
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    plt.show = show
    plt.figure = figure

    import traceback
    stack_call_position = traceback.extract_stack()[-2]
    stack_call_position.filename

    from matplotlib.axes._axes import Axes
    from matplotlib.figure import Figure
    def wrap(func, fig=True, text=""):
        def f(axes, *args, **kwargs):
            if args[2] == "New Text":
                if fig is True:
                    key = 'fig.texts[%d].new' % len(axes.texts)
                else:
                    index = axes.figure.axes.index(axes)
                    key = 'fig.axes[%d].texts[%d].new' % (index, len(axes.texts))
                    if plt.gca().get_label():
                        key = 'fig.ax_dict["%s"].texts[%d].new' % (plt.gca().get_label(), len(axes.texts))
                stack = traceback.extract_stack()
                for stack_item in stack:
                    if stack_item.filename == stack_call_position.filename:
                        keys_for_lines[stack_item.lineno] = key
                        break
            return func(axes, *args, **kwargs)
        return f
    #Axes.text = wrap(Axes.text, fig=False, text="New Text")
    #Axes.annotate = wrap(Axes.annotate, fig=False, text="New Annotation")

    #Figure.text = wrap(Figure.text, fig=True, text="New Text")
    #Figure.annotate = wrap(Figure.annotate, fig=True, text="New Annotation")
    plt.keys_for_lines = keys_for_lines


def show():
    global figures
    # set an application id, so that windows properly stacks them in the task bar
    if sys.platform[:3] == 'win':
        import ctypes
        myappid = 'rgerum.pylustrator'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # iterate over figures
    for figure in _pylab_helpers.Gcf.figs:
        # get the window
        window = _pylab_helpers.Gcf.figs[figure].canvas.window
        # warn about ticks not fitting tick labels
        warnAboutTicks(window.fig)
        # add dragger
        #FigureDragger(_pylab_helpers.Gcf.figs[figure].canvas.figure, [], [], "cm")
        DragManager(_pylab_helpers.Gcf.figs[figure].canvas.figure)
        window.update()
        # and show it
        window.show()
    # execute the application
    app.exec_()


def figure(num=None, size=None, *args, **kwargs):
    global figures
    # if num is not defined create a new number
    if num is None:
        num = len(_pylab_helpers.Gcf.figs)+1
    # if number is not defined
    if num not in _pylab_helpers.Gcf.figs.keys():
        # create a new window and store it
        canvas = PlotWindow(num, size, *args, **kwargs).canvas
        canvas.figure.number = num
        canvas.figure.clf()
        canvas.manager.num = num
        _pylab_helpers.Gcf.figs[num] = canvas.manager
    # get the canvas of the figure
    manager = _pylab_helpers.Gcf.figs[num]
    # set the size if it is defined
    if size is not None:
        _pylab_helpers.Gcf.figs[num].window.setGeometry(100, 100, size[0] * 80, size[1] * 80)
    # set the figure as the active figure
    _pylab_helpers.Gcf.set_active(manager)
    # return the figure
    return manager.canvas.figure

def warnAboutTicks(fig):
    import sys
    for index, ax in enumerate(fig.axes):
        ticks = ax.get_yticks()
        labels = [t.get_text() for t in ax.get_yticklabels()]
        for t, l in zip(ticks, labels):
            if l == "":
                continue
            try:
                l = float(l)
            except ValueError:
                pass
            if t != l:
                ax_name = ax.get_label()
                if ax_name == "":
                    ax_name = "#%d" % index
                else:
                    ax_name = '"' + ax_name + '"'
                print("Warning tick and label differ", t, l, "for axes", ax_name, file=sys.stderr)

""" Window """

class Linkable:

    def link(self, property_name,  signal=None, condition=None, direct=False):
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
                return setattr(target, parts[-1], v)
            self.setLinkedProperty = set
            self.getLinkedProperty = get
            self.serializeLinkedProperty = lambda x: "." + property_name + " = %s" % x
        else:
            self.setLinkedProperty = lambda text: getattr(self.element, "set_"+property_name)(text)
            self.getLinkedProperty = lambda: getattr(self.element, "get_"+property_name)()
            self.serializeLinkedProperty = lambda x: ".set_"+property_name+"(%s)" % x

        if condition is None:
            self.condition = lambda x: True
        else:
            self.condition = condition

        self.editingFinished.connect(self.updateLink)
        signal.connect(self.setTarget)

    def setTarget(self, element):
        self.element = element
        try:
            self.set(self.getLinkedProperty())
            self.setEnabled(self.condition(element))
        except AttributeError:
            self.hide()
        else:
            self.show()

    def updateLink(self):
        try:
            self.setLinkedProperty(self.get())
        except AttributeError:
            return
        if isinstance(self.element, mpl.figure.Figure):
            fig = self.element
        else:
            fig = self.element.figure
        fig.change_tracker.addChange(self.element, self.serializeLinkedProperty(self.getSerialized()))
        fig.canvas.draw()

    def set(self, value):
        pass

    def get(self):
        return None

    def getSerialized(self):
        return ""

class DimensionsWidget(QtWidgets.QWidget, Linkable):
    valueChanged = QtCore.Signal(tuple)
    transform = None
    noSignal = False

    def __init__(self, layout, text, join, unit):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.text = QtWidgets.QLabel(text)
        self.layout.addWidget(self.text)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.input1 = QtWidgets.QDoubleSpinBox()
        self.input1.setSuffix(" "+unit)
        self.input1.setSingleStep(0.1)
        self.input1.valueChanged.connect(self.onValueChanged)
        self.input1.setMaximum(99999)
        self.input1.setMinimum(-99999)
        self.layout.addWidget(self.input1)

        self.text2 = QtWidgets.QLabel(join)
        self.text2.setMaximumWidth(self.text2.fontMetrics().width(join))
        self.layout.addWidget(self.text2)

        self.input2 = QtWidgets.QDoubleSpinBox()
        self.input2.setSuffix(" "+unit)
        self.input2.setSingleStep(0.1)
        self.input2.valueChanged.connect(self.onValueChanged)
        self.input2.setMaximum(99999)
        self.input2.setMinimum(-99999)
        self.layout.addWidget(self.input2)

        self.editingFinished = self.valueChanged

    def setText(self, text):
        self.text.setText(text)

    def setUnit(self, unit):
        self.input1.setSuffix(" "+unit)
        self.input2.setSuffix(" "+unit)

    def setTransform(self, transform):
        self.transform = transform

    def onValueChanged(self, value):
        if not self.noSignal:
            self.valueChanged.emit(tuple(self.value()))

    def setValue(self, tuple):
        self.noSignal = True
        if self.transform:
            tuple = self.transform.transform(tuple)
        self.input1.setValue(tuple[0])
        self.input2.setValue(tuple[1])
        self.noSignal = False

    def value(self):
        tuple = (self.input1.value(), self.input2.value())
        if self.transform:
            tuple = self.transform.inverted().transform(tuple)
        return tuple

    def get(self):
        return self.value()

    def set(self, value):
        self.setValue(value)

    def getSerialized(self):
        return ", ".join([str(i) for i in self.get()])


class TextWidget(QtWidgets.QWidget, Linkable):
    editingFinished = QtCore.Signal()
    noSignal = False
    last_text = None

    def __init__(self, layout, text, multiline=False, horizontal=True):
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

    def setLabel(self, text):
        self.label.setLabel(text)

    def setText(self, text):
        self.noSignal = True
        text = text.replace("\n", "\\n")
        self.last_text = text
        if self.multiline:
            self.input1.setText(text)
        else:
            self.input1.setText(text)
        self.noSignal = False

    def text(self):
        text = self.input1.text()
        return text.replace("\\n", "\n")

    def get(self):
        return self.text()

    def set(self, value):
        self.setText(value)

    def getSerialized(self):
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


class CheckWidget(QtWidgets.QWidget):
    stateChanged = QtCore.Signal(int)
    noSignal = False

    def __init__(self, layout, text):
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

    def setChecked(self, state):
        self.noSignal = True
        self.input1.setChecked(state)
        self.noSignal = False

    def isChecked(self):
        return self.input1.isChecked()


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
        super(QtWidgets.QWidget, self).__init__()
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
            self.button.setStyleSheet("background-color: %s;" % value)
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


class TextPropertiesWidget(QtWidgets.QWidget):
    stateChanged = QtCore.Signal(int, str)
    noSignal = False

    def __init__(self, layout):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.buttons_align = []
        self.align_names = ["left", "center", "right"]
        for align in self.align_names:
            button = QtWidgets.QPushButton(qta.icon("fa.align-"+align), "")
            button.setCheckable(True)
            button.clicked.connect(lambda x, name=align: self.changeAlign(name))
            self.layout.addWidget(button)
            self.buttons_align.append(button)

        self.button_bold = QtWidgets.QPushButton(qta.icon("fa.bold"), "")
        self.button_bold.setCheckable(True)
        self.button_bold.clicked.connect(self.changeWeight)
        self.layout.addWidget(self.button_bold)

        self.button_italic = QtWidgets.QPushButton(qta.icon("fa.italic"), "")
        self.button_italic.setCheckable(True)
        self.button_italic.clicked.connect(self.changeStyle)
        self.layout.addWidget(self.button_italic)

        self.button_color = QColorWidget(self.layout)
        self.button_color.valueChanged.connect(self.changeColor)

        self.layout.addStretch()

        self.font_size = QtWidgets.QSpinBox()
        self.layout.addWidget(self.font_size)
        self.font_size.valueChanged.connect(self.changeFontSize)

        self.label = QtWidgets.QPushButton(qta.icon("fa.font"), "")#.pixmap(16))
        self.layout.addWidget(self.label)
        self.label.clicked.connect(self.selectFont)

        self.button_delete = QtWidgets.QPushButton(qta.icon("fa.trash"), "")
        self.button_delete.clicked.connect(self.delete)
        self.layout.addWidget(self.button_delete)

    def convertMplWeightToQtWeight(self, weight):
        weight_dict = {'normal': QtGui.QFont.Normal, 'bold': QtGui.QFont.Bold, 'heavy': QtGui.QFont.ExtraBold,
                       'light': QtGui.QFont.Light, 'ultrabold': QtGui.QFont.Black, 'ultralight': QtGui.QFont.ExtraLight}
        if weight in weight_dict:
            return weight_dict[weight]
        return weight_dict["normal"]

    def convertQtWeightToMplWeight(self, weight):
        weight_dict = {QtGui.QFont.Normal:'normal', QtGui.QFont.Bold:'bold', QtGui.QFont.ExtraBold:'heavy',
                       QtGui.QFont.Light:'light', QtGui.QFont.Black:'ultrabold', QtGui.QFont.ExtraLight:'ultralight'}
        if weight in weight_dict:
            return weight_dict[weight]
        return "normal"

    def selectFont(self):
        font0 = QtGui.QFont()
        font0.setFamily(self.target.get_fontname())
        font0.setWeight(self.convertMplWeightToQtWeight(self.target.get_weight()))
        font0.setItalic(self.target.get_style() == "italic")
        font0.setPointSizeF(self.target.get_fontsize())
        font, x = QtWidgets.QFontDialog.getFont(font0, self)

        self.target.set_fontname(font.family())
        self.target.figure.change_tracker.addChange(self.target, ".set_fontname(\"%s\")" % (self.target.get_fontname(),))

        if font.weight() != font0.weight():
            weight = self.convertQtWeightToMplWeight(font.weight())
            self.target.set_weight(weight)
            self.target.figure.change_tracker.addChange(self.target, ".set_weight(\"%s\")" % (weight,))

        if font.pointSizeF() != font0.pointSizeF():
            self.target.set_fontsize(font.pointSizeF())
            self.target.figure.change_tracker.addChange(self.target, ".set_fontsize(%f)" % (font.pointSizeF(),))

        if font.italic() != font0.italic():
            style = "italic" if font.italic() else "normal"
            self.target.set_style(style)
            self.target.figure.change_tracker.addChange(self.target, ".set_style(\"%s\")" % (style,))

        self.target.figure.canvas.draw()

    def setTarget(self, element):
        self.target = None
        self.font_size.setValue(element.get_fontsize())

        index_selected = self.align_names.index(element.get_ha())
        for index, button in enumerate(self.buttons_align):
            button.setChecked(index == index_selected)

        self.button_bold.setChecked(element.get_weight() == "bold")
        self.button_italic.setChecked(element.get_style() == "italic")
        self.button_color.setColor(element.get_color())

        self.target = element

    def delete(self):
        if self.target is not None:
            fig = self.target.figure
            fig.change_tracker.removeElement(self.target)
            self.target = None
            #self.target.set_visible(False)
            fig.canvas.draw()

    def changeWeight(self, checked):
        if self.target:
            element = self.target
            self.target = None

            element.set_weight("bold" if checked else "normal")
            element.figure.change_tracker.addChange(element, ".set_weight(\"%s\")" % ("bold" if checked else "normal",))

            self.target = element
            self.target.figure.canvas.draw()

    def changeStyle(self, checked):
        if self.target:
            element = self.target
            self.target = None

            element.set_style("italic" if checked else "normal")
            element.figure.change_tracker.addChange(element, ".set_style(\"%s\")" % ("italic" if checked else "normal",))

            self.target = element
            self.target.figure.canvas.draw()

    def changeColor(self, color):
        if self.target:
            element = self.target
            self.target = None

            element.set_color(color)
            element.figure.change_tracker.addChange(element, ".set_color(\"%s\")" % (color,))

            self.target = element
            self.target.figure.canvas.draw()

    def changeAlign(self, align):
        if self.target:
            element = self.target
            self.target = None

            index_selected = self.align_names.index(align)
            for index, button in enumerate(self.buttons_align):
                button.setChecked(index == index_selected)
            element.set_ha(align)
            element.figure.change_tracker.addChange(element, ".set_ha(\"%s\")" % align)

            self.target = element
            self.target.figure.canvas.draw()

    def changeFontSize(self, value):
        if self.target:
            self.target.set_fontsize(value)
            self.target.figure.change_tracker.addChange(self.target, ".set_fontsize(%d)" % value)
            self.target.figure.canvas.draw()


class myTreeWidgetItem(QtGui.QStandardItem):
    def __init__(self, parent=None):
        QtGui.QStandardItem.__init__(self, parent)

    def __lt__(self, otherItem):
        if self.sort is None:
            return 0
        return self.sort < otherItem.sort
        column = self.treeWidget().sortColumn()

        if column == 0 or column == 6 or column == 7 or column == 8:
            return float(self.text(column)) < float(otherItem.text(column))
        else:
            return self.text(column) < otherItem.text(column)


class MyTreeView(QtWidgets.QTreeView):
    item_selected = lambda x, y: 0
    item_clicked = lambda x, y: 0
    item_activated = lambda x, y: 0
    item_hoverEnter = lambda x, y: 0
    item_hoverLeave = lambda x, y: 0

    last_selection = None
    last_hover = None

    def __init__(self, parent, layout, fig):
        super(QtWidgets.QTreeView, self).__init__()

        self.fig = fig

        layout.addWidget(self)

        # start a list for backwards search (from marker entry back to tree entry)
        self.marker_modelitems = {}
        self.marker_type_modelitems = {}

        # model for tree view
        self.model = QtGui.QStandardItemModel(0, 0)

        # some settings for the tree
        self.setUniformRowHeights(True)
        self.setHeaderHidden(True)
        self.setAnimated(True)
        self.setModel(self.model)
        self.expanded.connect(self.TreeExpand)
        self.clicked.connect(self.treeClicked)
        self.activated.connect(self.treeActivated)
        self.selectionModel().selectionChanged.connect(self.selectionChanged)

        # add context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # add hover highlight
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)

        self.item_lookup = {}

        self.expand(None)

    def selectionChanged(self, selection, y):
        try:
            entry = selection.indexes()[0].model().itemFromIndex(selection.indexes()[0]).entry
        except IndexError:
            entry = None
        if self.last_selection != entry:
            self.last_selection = entry
            self.item_selected(entry)

    def setCurrentIndex(self, entry):
        while entry:
            item = self.getItemFromEntry(entry)
            if item is not None:
                super(QtWidgets.QTreeView, self).setCurrentIndex(item.index())
                return
            try:
                entry = entry.tree_parent
            except AttributeError:
                return

    def treeClicked(self, index):
        # upon selecting one of the tree elements
        data = index.model().itemFromIndex(index).entry
        return self.item_clicked(data)

    def treeActivated(self, index):
        # upon selecting one of the tree elements
        data = index.model().itemFromIndex(index).entry
        return self.item_activated(data)

    def eventFilter(self, object, event):
        """ event filter for tree view port to handle mouse over events and marker highlighting"""
        if event.type() == QtCore.QEvent.HoverMove:
            index = self.indexAt(event.pos())
            try:
                item = index.model().itemFromIndex(index)
                entry = item.entry
            except:
                item = None
                entry = None

            # check for new item
            if entry != self.last_hover:

                # deactivate last hover item
                if self.last_hover is not None:
                    self.item_hoverLeave(self.last_hover)

                # activate current hover item
                if entry is not None:
                    self.item_hoverEnter(entry)

                self.last_hover = entry
                return True

        return False

    def queryToExpandEntry(self, entry):
        if entry is None:
            return [self.fig]
        return entry.get_children()

    def getParentEntry(self, entry):
        return entry.tree_parent

    def getNameOfEntry(self, entry):
        try:
            return str(entry)
        except AttributeError:
            return "unknown"

    def getIconOfEntry(self, entry):
        if getattr(entry, "_draggable", None):
            if entry._draggable.connected:
                return qta.icon("fa.hand-paper-o")
        return QtGui.QIcon()

    def getEntrySortRole(self, entry):
        return None

    def getKey(self, entry):
        return entry

    def getItemFromEntry(self, entry):
        if entry is None:
            return None
        key = self.getKey(entry)
        try:
            return self.item_lookup[key]
        except KeyError:
            return None

    def setItemForEntry(self, entry, item):
        key = self.getKey(entry)
        self.item_lookup[key] = item

    def expand(self, entry, force_reload=True):
        query = self.queryToExpandEntry(entry)
        parent_item = self.getItemFromEntry(entry)
        parent_entry = entry

        if parent_item:
            if parent_item.expanded is False:
                # remove the dummy child
                parent_item.removeRow(0)
                parent_item.expanded = True
            # force_reload: delete all child entries and re query content from DB
            elif force_reload:
                # delete child entries
                parent_item.removeRows(0, parent_item.rowCount())
            else:
                return

        # add all marker types
        row = -1
        for row, entry in enumerate(query):
            entry.tree_parent = parent_entry
            if 1:
                if(isinstance(entry, mpl.spines.Spine) or
                   isinstance(entry, mpl.axis.XAxis) or
                   isinstance(entry, mpl.axis.YAxis)):
                    continue
                if isinstance(entry, mpl.text.Text) and entry.get_text() == "":
                    continue
                try:
                    if entry == parent_entry.patch:
                        continue
                except AttributeError:
                    pass
                try:
                    label = entry.get_label()
                    if label == "_tmp_snap" or label == "grabber":
                        continue
                except AttributeError:
                    pass
            self.addChild(parent_item, entry)

    def addChild(self, parent_item, entry, row=None):
        if parent_item is None:
            parent_item = self.model

        # add item
        item = myTreeWidgetItem(self.getNameOfEntry(entry))
        item.expanded = False
        item.entry = entry

        item.setIcon(self.getIconOfEntry(entry))
        item.setEditable(False)
        item.sort = self.getEntrySortRole(entry)

        if parent_item is None:
            if row is None:
                row = self.model.rowCount()
            self.model.insertRow(row)
            self.model.setItem(row, 0, item)
        else:
            if row is None:
                parent_item.appendRow(item)
            else:
                parent_item.insertRow(row, item)
        self.setItemForEntry(entry, item)

        # add dummy child
        if self.queryToExpandEntry(entry) is not None and len(self.queryToExpandEntry(entry)):
            child = QtGui.QStandardItem("loading")
            child.entry = None
            child.setEditable(False)
            child.setIcon(qta.icon("fa.hourglass-half"))
            item.appendRow(child)
            item.expanded = False
        return item

    def TreeExpand(self, index):
        # Get item and entry
        item = index.model().itemFromIndex(index)
        entry = item.entry
        thread = None

        # Expand
        if item.expanded is False:
            self.expand(entry)
            #thread = Thread(target=self.expand, args=(entry,))

        # Start thread as daemonic
        if thread:
            thread.setDaemon(True)
            thread.start()

    def updateEntry(self, entry, update_children=False, insert_before=None, insert_after=None):
        # get the tree view item for the database entry
        item = self.getItemFromEntry(entry)
        # if we haven't one yet, we have to create it
        if item is None:
            # get the parent entry
            parent_entry = self.getParentEntry(entry)
            parent_item = None
            # if we have a parent and are not at the top level try to get the corresponding item
            if parent_entry:
                parent_item = self.getItemFromEntry(parent_entry)
                # parent item not in list or not expanded, than we don't need to update it because it is not shown
                if parent_item is None or parent_item.expanded is False:
                    if parent_item:
                        parent_item.setText(self.getNameOfEntry(parent_entry))
                    return

            # define the row where the new item should be
            row = None
            if insert_before:
                row = self.getItemFromEntry(insert_before).row()
            if insert_after:
                row = self.getItemFromEntry(insert_after).row() + 1

            # add the item as a child of its parent
            self.addChild(parent_item, entry, row)
            if parent_item:
                if row is None:
                    parent_item.sortChildren(0)
                if parent_entry:
                    parent_item.setText(self.getNameOfEntry(parent_entry))
        else:
            # check if we have to change the parent
            parent_entry = self.getParentEntry(entry)
            parent_item = self.getItemFromEntry(parent_entry)
            if parent_item != item.parent():
                # remove the item from the old position
                if item.parent() is None:
                    self.model.takeRow(item.row())
                else:
                    item.parent().takeRow(item.row())

                # determine a potential new position
                row = None
                if insert_before:
                    row = self.getItemFromEntry(insert_before).row()
                if insert_after:
                    row = self.getItemFromEntry(insert_after).row() + 1

                # move the item to the new position
                if parent_item is None:
                    if row is None:
                        row = self.model.rowCount()
                    self.model.insertRow(row)
                    self.model.setItem(row, 0, item)
                else:
                    if row is None:
                        parent_item.appendRow(item)
                    else:
                        parent_item.insertRow(row, item)

            # update the items name, icon and children
            item.setIcon(self.getIconOfEntry(entry))
            item.setText(self.getNameOfEntry(entry))
            if update_children:
                self.expand(entry, force_reload=True)

    def deleteEntry(self, entry):
        item = self.getItemFromEntry(entry)
        if item is None:
            return

        parent_item = item.parent()
        if parent_item:
            parent_entry = parent_item.entry

        key = self.getKey(entry)
        del self.item_lookup[key]

        if parent_item is None:
            self.model.removeRow(item.row())
        else:
            item.parent().removeRow(item.row())

        if parent_item:
            name = self.getNameOfEntry(parent_entry)
            if name is not None:
                parent_item.setText(name)


class QTickEdit(QtWidgets.QWidget):
    def __init__(self, axis, signal_target_changed):
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("Figure - "+axis+"-Axis - Ticks - Pylustrator")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", "ticks.ico")))
        self.layout = QtWidgets.QVBoxLayout(self)
        self.axis = axis

        self.label = QtWidgets.QLabel("Ticks can be specified, one tick pre line.\nOptionally a label can be provided, e.g. 1 \"First\",")
        self.layout.addWidget(self.label)

        self.layout2 = QtWidgets.QHBoxLayout()
        self.layout.addLayout(self.layout2)

        self.input_ticks = TextWidget(self.layout2, axis + "-Ticks:", multiline=True, horizontal=False)
        self.input_ticks.editingFinished.connect(self.ticksChanged)

        self.input_ticks2 = TextWidget(self.layout2, axis + "-Ticks (minor):", multiline=True, horizontal=False)
        self.input_ticks2.editingFinished.connect(self.ticksChanged2)

        self.input_scale = ComboWidget(self.layout, axis + "-Scale", ["linear", "log", "symlog", "logit"])
        self.input_scale.link(axis + "scale", signal_target_changed)

        self.input_font = TextPropertiesWidget(self.layout)

        self.input_labelpad = NumberWidget(self.layout, axis+"-Labelpad", min=-999)
        self.input_labelpad.link(axis + "axis.labelpad", signal_target_changed, direct=True)

        self.button_ok = QtWidgets.QPushButton("Ok")
        self.layout.addWidget(self.button_ok)
        self.button_ok.clicked.connect(self.hide)

    def parseTickLabel(self, line):
        import re
        line = line.replace("−", "-")
        match = re.match(r"\$\\mathdefault{(([-.\d]*)\\times)?([-.\d]+)\^{([-.\d]+)}}\$", line)
        if match:
            _, factor, base, exponent = match.groups()
            if factor is not None:
                number = float(factor) * float(base)**float(exponent)
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

    def formatTickLabel(self, line):
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


    def setTarget(self, element):
        self.element = element
        self.fig = element.figure
        min, max = getattr(self.element, "get_" + self.axis + "lim")()
        self.range = [min, max]

        ticks = getattr(self.element, "get_"+self.axis+"ticks")()
        labels = getattr(self.element, "get_" + self.axis + "ticklabels")()
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

        self.input_font.setTarget(getattr(self.element, "get_"+self.axis+"axis")().get_label())

    def parseTicks(self, string):
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
                    ticks.append(tick)
                    labels.append(label)
        except Exception as err:
            pass
        return ticks, labels

    def str(self, object):
        if str(object) == "nan":
            return "np.nan"
        return str(object)

    def ticksChanged2(self):
        ticks, labels = self.parseTicks(self.input_ticks2.text())

        getattr(self.element, "set_" + self.axis + "lim")(self.range)
        getattr(self.element, "set_" + self.axis + "ticks")(ticks, minor=True)
        getattr(self.element, "set_" + self.axis + "ticklabels")(labels, minor=True)
        min, max = getattr(self.element, "get_" + self.axis + "lim")()
        if min != self.range[0] or max != self.range[1]:
            self.fig.change_tracker.addChange(self.element,
                                              ".set_" + self.axis + "lim(%s, %s)" % (str(min), str(max)))
        else:
            self.fig.change_tracker.addChange(self.element,
                                              ".set_" + self.axis + "lim(%s, %s)" % (str(self.range[0]), str(self.range[1])))

        # self.setTarget(self.element)
        self.fig.change_tracker.addChange(self.element,
                                          ".set_" + self.axis + "ticks([%s], minor=True)" % ", ".join(self.str(t) for t in ticks), self.element, ".set_" + self.axis + "ticks_minor")
        self.fig.change_tracker.addChange(self.element, ".set_" + self.axis + "ticklabels([%s], minor=True)" % ", ".join(
            '"' + l + '"' for l in labels), self.element, ".set_" + self.axis + "labels_minor")
        self.fig.canvas.draw()

    def ticksChanged(self):
        ticks, labels = self.parseTicks(self.input_ticks.text())

        getattr(self.element, "set_" + self.axis + "lim")(self.range)
        getattr(self.element, "set_" + self.axis + "ticks")(ticks)
        getattr(self.element, "set_" + self.axis + "ticklabels")(labels)
        min, max = getattr(self.element, "get_" + self.axis + "lim")()
        if min != self.range[0] or max != self.range[1]:
            self.fig.change_tracker.addChange(self.element,
                                              ".set_" + self.axis + "lim(%s, %s)" % (str(min), str(max)))
        else:
            self.fig.change_tracker.addChange(self.element,
                                              ".set_" + self.axis + "lim(%s, %s)" % (str(self.range[0]), str(self.range[1])))

        #self.setTarget(self.element)
        self.fig.change_tracker.addChange(self.element, ".set_" + self.axis + "ticks([%s])" % ", ".join(self.str(t) for t in ticks))
        self.fig.change_tracker.addChange(self.element, ".set_" + self.axis + "ticklabels([%s])" % ", ".join('"'+l+'"' for l in labels))
        self.fig.canvas.draw()

class QAxesProperties(QtWidgets.QWidget):
    def __init__(self, layout, axis, signal_target_changed):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.targetChanged = signal_target_changed
        self.targetChanged.connect(self.setTarget)

        self.input_label = TextWidget(self.layout, axis+"-Label:")
        self.input_label.link(axis+"label", signal=self.targetChanged)

        self.input_lim = DimensionsWidget(self.layout, axis+"-Lim:", "-", "")
        self.input_lim.link(axis+"lim", signal=self.targetChanged)

        self.button_ticks = QtWidgets.QPushButton(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", "ticks.ico")), "")
        self.button_ticks.clicked.connect(self.showTickWidget)
        self.layout.addWidget(self.button_ticks)

        self.tick_edit = QTickEdit(axis, signal_target_changed)

    def showTickWidget(self):
        self.tick_edit.setTarget(self.element)
        self.tick_edit.show()

    def setTarget(self, element):
        self.element = element

        if isinstance(element, Axes):
            self.show()
        else:
            self.hide()


class QItemProperties(QtWidgets.QWidget):
    targetChanged = QtCore.Signal('PyQt_PyObject')
    valueChanged = QtCore.Signal(tuple)
    element = None
    transform = None
    transform_index = 0
    scale_type = 0

    def __init__(self, layout, fig, tree, parent):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.tree = tree
        self.parent = parent

        self.label = QtWidgets.QLabel()
        self.layout.addWidget(self.label)

        self.input_transform = RadioWidget(self.layout, ["cm", "in", "px", "none"])
        self.input_transform.stateChanged.connect(self.changeTransform)

        self.input_picker = CheckWidget(self.layout, "Pickable:")
        self.input_picker.stateChanged.connect(self.changePickable)

        self.input_position = DimensionsWidget(self.layout, "Position:", "x", "cm")
        self.input_position.valueChanged.connect(self.changePos)

        self.input_shape = DimensionsWidget(self.layout, "Size:", "x", "cm")
        self.input_shape.valueChanged.connect(self.changeSize)

        self.input_shape_transform = RadioWidget(self.layout, ["scale", "bottom right", "top left"])
        self.input_shape_transform.stateChanged.connect(self.changeTransform2)

        self.input_text = TextWidget(self.layout, "Text:")
        self.input_text.link("text", self.targetChanged)

        self.input_rotation = NumberWidget(self.layout, "Rotation:")
        self.input_rotation.link("rotation", self.targetChanged)
        self.input_rotation.input1.setRange(-360, 360)

        self.input_xaxis = QAxesProperties(self.layout, "x", self.targetChanged)
        self.input_yaxis = QAxesProperties(self.layout, "y", self.targetChanged)

        self.input_font_properties = TextPropertiesWidget(self.layout)


        layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(layout)

        condition_line = lambda x: getattr(x, "get_linestyle")() not in ["None", " ", ""]
        condition_marker = lambda x: getattr(x, "get_marker")() not in ["None", " ", ""]

        TextWidget(layout, "Linestyle:").link("linestyle", self.targetChanged)

        NumberWidget(layout, "Linewidth:").link("linewidth", self.targetChanged, condition=condition_line)#lambda x: getattr(x, "get_linestyle") not in ["None", " ", ""])

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

        self.button_add_rectangle = QtWidgets.QPushButton("add rectangle")
        self.layout_buttons.addWidget(self.button_add_rectangle)
        self.button_add_rectangle.clicked.connect(self.buttonAddRectangleClicked)

        self.button_add_arrow = QtWidgets.QPushButton("add arrow")
        self.layout_buttons.addWidget(self.button_add_arrow)
        self.button_add_arrow.clicked.connect(self.buttonAddArrowClicked)

        self.button_despine = QtWidgets.QPushButton("despine")
        self.layout_buttons.addWidget(self.button_despine)
        self.button_despine.clicked.connect(self.buttonDespineClicked)

        self.fig = fig

    def buttonAddImageClicked(self):
        fig = self.fig
        def addChange(element, command):
            fig.change_tracker.addChange(element, command)
            return eval(getReference(element)+command)

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
        addChange(axes, ".spines['right'].set_visible(False)")
        addChange(axes, ".spines['left'].set_visible(False)")
        addChange(axes, ".spines['top'].set_visible(False)")
        addChange(axes, ".spines['bottom'].set_visible(False)")

        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(axes)
        self.fig.figure_dragger.select_element(axes)
        self.fig.canvas.draw()
        self.setElement(axes)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddTextClicked(self):
        if isinstance(self.element, Axes):
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transAxes)
            self.fig.change_tracker.addChange(self.element,
                                              ".text(0.5, 0.5, 'New Text', transform=%s.transAxes)  # id=%s.new" % (
                                              getReference(self.element), getReference(text)), text, ".new")
        if isinstance(self.element, Figure):
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transFigure)
            self.fig.change_tracker.addChange(self.element,
                                              ".text(0.5, 0.5, 'New Text', transform=%s.transFigure)  # id=%s.new" % (
                                              getReference(self.element), getReference(text)), text, ".new")
        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(text)
        self.fig.canvas.draw()
        self.fig.figure_dragger.select_element(text)
        self.setElement(text)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddAnnotationClicked(self):
        text = self.element.annotate("New Annotation", (self.element.get_xlim()[0], self.element.get_ylim()[0]), (np.mean(self.element.get_xlim()), np.mean(self.element.get_ylim())), arrowprops=dict(arrowstyle="->"))
        self.fig.change_tracker.addChange(self.element, ".annotate('New Annotation', %s, %s, arrowprops=dict(arrowstyle='->'))  # id=%s.new" % (text.xy, text.get_position(), getReference(text)),
                                          text, ".new")

        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(text)
        self.fig.figure_dragger.select_element(text)
        self.fig.canvas.draw()
        self.setElement(text)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddRectangleClicked(self):
        p = mpl.patches.Rectangle((self.element.get_xlim()[0], self.element.get_ylim()[0]),
                                        width=np.mean(self.element.get_xlim()), height=np.mean(self.element.get_ylim()),)
        self.element.add_patch(p)

        self.fig.change_tracker.addChange(self.element,
                                          ".add_patch(mpl.patches.Rectangle(%s, width=%s, height=%s))  # id=%s.new" % (
                                          p.get_xy(), p.get_width(), p.get_height(), getReference(p)),
                                          p, ".new")

        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(p)
        self.fig.figure_dragger.select_element(p)
        self.fig.canvas.draw()
        self.setElement(p)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddArrowClicked(self):
        p = mpl.patches.FancyArrowPatch((self.element.get_xlim()[0], self.element.get_ylim()[0]), (np.mean(self.element.get_xlim()), np.mean(self.element.get_ylim())), arrowstyle="Simple,head_length=10,head_width=10,tail_width=2", facecolor="black", clip_on=False, zorder=2)
        self.element.add_patch(p)

        self.fig.change_tracker.addChange(self.element, ".add_patch(mpl.patches.FancyArrowPatch(%s, %s, arrowstyle='Simple,head_length=10,head_width=10,tail_width=2', facecolor='black', clip_on=False, zorder=2))  # id=%s.new" % (p._posA_posB[0], p._posA_posB[1], getReference(p)),
                                          p, ".new")

        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(p)
        self.fig.figure_dragger.select_element(p)
        self.fig.canvas.draw()
        self.setElement(p)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def changeTransform(self, transform_index, name):
        self.transform_index = transform_index
        if name == "none":
            name = ""
        self.input_shape.setUnit(name)
        self.input_position.setUnit(name)
        self.setElement(self.element)

    def changeTransform2(self, state, name):
        self.scale_type = state

    def changePos(self, value):
        pos = self.element.get_position()
        try:
            w, h = pos.width, pos.height
            pos.x0 = value[0]
            pos.y0 = value[1]
            pos.x1 = value[0]+w
            pos.y1 = value[1]+h

            self.fig.change_tracker.addChange(self.element, ".set_position([%f, %f, %f, %f])" % (pos.x0, pos.y0, pos.width, pos.height))
        except AttributeError:
            pos = value

            self.fig.change_tracker.addChange(self.element, ".set_position([%f, %f])" % (pos[0], pos[1]))
        self.element.set_position(pos)
        self.fig.canvas.draw()

    def changeSize(self, value):
        if isinstance(self.element, Figure):

            if self.scale_type == 0:
                self.fig.set_size_inches(value)
                self.fig.change_tracker.addChange(self.element, ".set_size_inches(%f/2.54, %f/2.54, forward=True)" % (value[0]*2.54, value[1]*2.54))
            else:
                if self.scale_type == 1:
                    changeFigureSize(value[0], value[1], fig=self.fig)
                elif self.scale_type == 2:
                    changeFigureSize(value[0], value[1], cut_from_top=True, cut_from_left=True, fig=self.fig)
                self.fig.change_tracker.addChange(self.element, ".set_size_inches(%f/2.54, %f/2.54, forward=True)" % (value[0] * 2.54, value[1] * 2.54))
                for axes in self.fig.axes:
                    pos = axes.get_position()
                    self.fig.change_tracker.addChange(axes, ".set_position([%f, %f, %f, %f])" % (pos.x0, pos.y0, pos.width, pos.height))
                for text in self.fig.texts:
                    pos = text.get_position()
                    self.fig.change_tracker.addChange(text, ".set_position([%f, %f])" % (pos[0], pos[1]))


            self.fig.canvas.draw()
            self.fig.widget.updateGeometry()
            self.parent.updateFigureSize()
        else:
            pos = self.element.get_position()
            pos.x1 = pos.x0 + value[0]
            pos.y1 = pos.y0 + value[1]
            self.element.set_position(pos)

            self.fig.change_tracker.addChange(self.element, ".set_position([%f, %f, %f, %f])" % (pos.x0, pos.y0, pos.width, pos.height))

            self.fig.canvas.draw()

    def buttonDespineClicked(self):
        commands = [".spines['right'].set_visible(False)", 
                    ".spines['top'].set_visible(False)"]
        for command in commands:
            eval("self.element"+command)
            self.fig.change_tracker.addChange(self.element, command)
        self.fig.canvas.draw()

    def changePickable(self):
        if self.input_picker.isChecked():
            self.element._draggable.connect()
        else:
            self.element._draggable.disconnect()
        self.tree.updateEntry(self.element)

    def getTransform(self, element):
        if isinstance(element, Figure):
            if self.transform_index == 0:
                return transforms.Affine2D().scale(2.54, 2.54)
            return None
        if isinstance(element, Axes):
            if self.transform_index == 0:
                return transforms.Affine2D().scale(2.54, 2.54) + element.figure.dpi_scale_trans.inverted() + element.figure.transFigure
            if self.transform_index == 1:
                return element.figure.dpi_scale_trans.inverted() + element.figure.transFigure
            if self.transform_index == 2:
                return element.figure.transFigure
            return None
        if self.transform_index == 0:
            return transforms.Affine2D().scale(2.54,
                                               2.54) + element.figure.dpi_scale_trans.inverted() + element.get_transform()
        if self.transform_index == 1:
            return element.figure.dpi_scale_trans.inverted() + element.get_transform()
        if self.transform_index == 2:
            return element.get_transform()
        return None

    def setElement(self, element):
        self.label.setText(str(element))
        self.element = element
        try:
            element._draggable
            self.input_picker.setChecked(element._draggable.connected)
            self.input_picker.show()
        except AttributeError:
            self.input_picker.hide()

        self.input_shape_transform.hide()
        self.input_transform.hide()
        self.button_add_annotation.hide()
        self.button_add_rectangle.hide()
        self.button_despine.hide()
        self.button_add_image.hide()
        self.button_add_arrow.hide()
        if isinstance(element, Figure):
            pos = element.get_size_inches()
            self.input_shape.setTransform(self.getTransform(element))
            self.input_shape.setValue((pos[0], pos[1]))
            self.input_shape.show()
            self.input_transform.show()
            self.input_shape_transform.show()
            self.button_add_text.show()
            self.button_add_image.show()
        elif isinstance(element, Axes):
            pos = element.get_position()
            self.input_shape.setTransform(self.getTransform(element))
            self.input_shape.setValue((pos.width, pos.height))
            self.input_transform.show()
            self.input_shape.show()
            self.button_add_text.show()
            self.button_add_annotation.show()
            self.button_despine.show()
            self.button_add_arrow.show()
            self.button_add_rectangle.show()
        else:
            self.input_shape.hide()
            self.button_add_text.hide()

        try:
            pos = element.get_position()
            self.input_position.setTransform(self.getTransform(element))
            try:
                self.input_position.setValue(pos)
            except Exception as err:
                self.input_position.setValue((pos.x0, pos.y0))
            self.input_transform.show()
            self.input_position.show()
        except:
            self.input_position.hide()

        try:
            self.input_font_properties.show()
            self.input_font_properties.setTarget(element)
        except AttributeError:
            self.input_font_properties.hide()

        self.targetChanged.emit(element)


class PlotWindow(QtWidgets.QWidget):
    fitted_to_view = False

    def __init__(self, number, size, *args, **kwargs):
        QtWidgets.QWidget.__init__(self)

        self.canvas_canvas = QtWidgets.QWidget()
        self.canvas_canvas.setMinimumHeight(400)
        self.canvas_canvas.setMinimumWidth(400)
        self.canvas_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.canvas_canvas.setStyleSheet("background:white")
        self.canvas_canvas.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.shadow = QtWidgets.QLabel(self.canvas_canvas)

        self.canvas_container = QtWidgets.QWidget(self.canvas_canvas)
        self.canvas_wrapper_layout = QtWidgets.QHBoxLayout()
        self.canvas_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_container.setLayout(self.canvas_wrapper_layout)

        self.canvas_container.setStyleSheet("background:blue")

        self.x_scale = QtWidgets.QLabel(self.canvas_canvas)
        self.y_scale = QtWidgets.QLabel(self.canvas_canvas)

        self.canvas = MatplotlibWidget(self, number, size=size)
        self.canvas.window = self
        self.canvas_wrapper_layout.addWidget(self.canvas)
        self.fig = self.canvas.figure
        self.fig.widget = self.canvas

        def mousePress(event):
            self.canvas.mousePressEvent(event)

        self.canvas_canvas.mousePressEvent = mousePress

        def mouseRelease(event):
            self.canvas.mouseReleaseEvent(event)

        self.canvas_canvas.mouseReleaseEvent = mouseRelease

        # widget layout and elements
        self.setWindowTitle("Figure %s - Pylustrator" % number)
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", "logo.ico")))
        self.layout_main = QtWidgets.QHBoxLayout(self)

        #
        self.layout_tools = QtWidgets.QVBoxLayout()
        self.layout_tools.setContentsMargins(0, 0, 0, 0)
        self.layout_main.addLayout(self.layout_tools)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        widget = QtWidgets.QWidget()
        self.layout_tools.addWidget(widget)
        self.layout_tools = QtWidgets.QVBoxLayout(widget)
        widget.setMaximumWidth(350)
        widget.setMinimumWidth(350)

        self.treeView = MyTreeView(self, self.layout_tools, self.fig)
        self.treeView.item_selected = self.elementSelected

        self.input_properties = QItemProperties(self.layout_tools, self.fig, self.treeView, self)

        # add plot layout
        self.layout_plot = QtWidgets.QVBoxLayout()
        self.layout_main.addLayout(self.layout_plot)

        # add plot canvas
        self.layout_plot.addWidget(self.canvas_canvas)

        # add toolbar
        #self.navi_toolbar = NavigationToolbar(self.canvas, self)
        #self.layout_plot.addWidget(self.navi_toolbar)

        self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)

        self.fig.canvas.mpl_connect('scroll_event', self.scroll_event)
        self.fig.canvas.mpl_connect('key_press_event', self.canvas_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.canvas_key_release)
        self.control_modifier = False

        self.fig.canvas.mpl_connect('button_press_event', self.button_press_event)
        self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move_event)
        self.fig.canvas.mpl_connect('button_release_event', self.button_release_event)
        self.drag = None
        
        self.footer_layout = QtWidgets.QHBoxLayout()
        self.layout_plot.addLayout(self.footer_layout)
        
        self.footer_label = QtWidgets.QLabel("")
        self.footer_layout.addWidget(self.footer_label)

        self.footer_layout.addStretch()

        self.footer_label2 = QtWidgets.QLabel("")
        self.footer_layout.addWidget(self.footer_label2)

        #self.layout_plot.addStretch()
        #self.layout_main.addStretch()

    def updateRuler(self):
        trans = transforms.Affine2D().scale(1./2.54, 1./2.54) + self.fig.dpi_scale_trans
        l = 17
        l1 = 13
        l2 = 6
        l3 = 4

        w = self.canvas_canvas.width()
        h = self.canvas_canvas.height()

        self.pixmapX = QtGui.QPixmap(w, l)
        self.pixmapY = QtGui.QPixmap(l, h)

        self.pixmapX.fill(QtGui.QColor("#f0f0f0"))
        self.pixmapY.fill(QtGui.QColor("#f0f0f0"))

        painterX = QtGui.QPainter(self.pixmapX)
        painterY = QtGui.QPainter(self.pixmapY)

        painterX.setPen(QtGui.QPen(QtGui.QColor("black"), 1))
        painterY.setPen(QtGui.QPen(QtGui.QColor("black"), 1))

        offset = self.canvas_container.pos().x()
        start_x = np.floor(trans.inverted().transform((-offset, 0))[0])
        end_x = np.ceil(trans.inverted().transform((-offset+w, 0))[0])
        dx = 0.1
        for i, pos_cm in enumerate(np.arange(start_x, end_x, dx)):
            x = (trans.transform((pos_cm, 0))[0] + offset)
            if i % 10 == 0:
                painterX.drawLine(x, l - l1 - 1, x, l - 1)
                text = str("%d" % np.round(pos_cm))
                o = 0
                painterX.drawText(x+3, o, self.fontMetrics().width(text), o+self.fontMetrics().height(), QtCore.Qt.AlignLeft,
                                 text)
            elif i % 2 == 0:
                painterX.drawLine(x, l - l2 - 1, x, l - 1)
            else:
                painterX.drawLine(x, l - l3 - 1, x, l - 1)
        painterX.drawLine(0, l-2, w, l-2)
        painterX.setPen(QtGui.QPen(QtGui.QColor("white"), 1))
        painterX.drawLine(0, l-1, w, l-1)
        self.x_scale.setPixmap(self.pixmapX)
        self.x_scale.setMinimumSize(w, l)
        self.x_scale.setMaximumSize(w, l)

        #height_cm = self.fig.get_size_inches()[1]*2.45
        offset = self.canvas_container.pos().y() + self.canvas_container.height()
        start_y = np.floor(trans.inverted().transform((0, +offset-h))[1])
        end_y = np.ceil(trans.inverted().transform((0, +offset))[1])
        dy = 0.1
        for i, pos_cm in enumerate(np.arange(start_y, end_y, dy)):
            y = (-trans.transform((0, pos_cm))[1] + offset)
            if i % 10 == 0:
                painterY.drawLine(l - l1 - 1, y, l - 1, y)
                text = str("%d" % np.round(pos_cm))
                o = 0
                painterY.drawText(o, y+3, o+self.fontMetrics().width(text), self.fontMetrics().height(), QtCore.Qt.AlignRight,
                                 text)
            elif i % 2 == 0:
                painterY.drawLine(l - l2 - 1, y, l - 1, y)
            else:
                painterY.drawLine(l - l3 - 1, y, l - 1, y)
        painterY.drawLine(l-2, 0, l-2, h)
        painterY.setPen(QtGui.QPen(QtGui.QColor("white"), 1))
        painterY.drawLine(l-1, 0, l-1, h)
        painterY.setPen(QtGui.QPen(QtGui.QColor("#f0f0f0"), 0))
        painterY.setBrush(QtGui.QBrush(QtGui.QColor("#f0f0f0")))
        painterY.drawRect(0, 0, l, l)
        self.y_scale.setPixmap(self.pixmapY)
        self.y_scale.setMinimumSize(l, h)
        self.y_scale.setMaximumSize(l, h)

        w, h = self.canvas.get_width_height()

        self.pixmap = QtGui.QPixmap(w+100, h+10)

        self.pixmap.fill(QtGui.QColor("transparent"))

        painter = QtGui.QPainter(self.pixmap)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#666666")))
        painter.drawRect(2, 2, w + 2,  h + 2)
        painter.drawRect(0, 0, w+2, h+2)

        p = self.canvas_container.pos()
        self.shadow.setPixmap(self.pixmap)
        self.shadow.move(p.x()-1, p.y()-1)
        self.shadow.setMinimumSize(w+100, h+10)
        self.shadow.setMaximumSize(w+100, h+10)

    def showEvent(self, event):
        self.fitToView()
        self.updateRuler()

    def resizeEvent(self, event):
        if self.fitted_to_view:
            self.fitToView(True)
        else:
            self.updateRuler()

    def button_press_event(self, event):
        if event.button == 2:
            self.drag = np.array([event.x, event.y])

    def mouse_move_event(self, event):
        if self.drag is not None:
            pos = np.array([event.x, event.y])
            offset = pos - self.drag
            offset[1] = -offset[1]
            self.moveCanvasCanvas(*offset)
        trans = transforms.Affine2D().scale(2.54, 2.54) + self.fig.dpi_scale_trans.inverted()
        pos = trans.transform((event.x, event.y))
        self.footer_label.setText("%.2f, %.2f (cm) [%d, %d]" % (pos[0], pos[1], event.x, event.y))

        if event.ydata is not None:
            self.footer_label2.setText("%.2f, %.2f" % (event.xdata, event.ydata))
        else:
            self.footer_label2.setText("")

    def button_release_event(self, event):
        if event.button == 2:
            self.drag = None

    def canvas_key_press(self, event):
        if event.key == "control":
            self.control_modifier = True

    def canvas_key_release(self, event):
        if event.key == "control":
            self.control_modifier = False

    def moveCanvasCanvas(self, offset_x, offset_y):
        p = self.canvas_container.pos()
        self.canvas_container.move(p.x() + offset_x, p.y() + offset_y)

        self.updateRuler()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = True
        if event.key() == QtCore.Qt.Key_Left:
            self.moveCanvasCanvas(-10, 0)
        if event.key() == QtCore.Qt.Key_Right:
            self.moveCanvasCanvas(10, 0)
        if event.key() == QtCore.Qt.Key_Up:
            self.moveCanvasCanvas(0, -10)
        if event.key() == QtCore.Qt.Key_Down:
            self.moveCanvasCanvas(0, 10)

        if event.key() == QtCore.Qt.Key_F:
            self.fitToView(True)

    def fitToView(self, change_dpi=False):
        self.fitted_to_view = True
        if change_dpi:
            w, h = self.canvas.get_width_height()
            factor = min( (self.canvas_canvas.width() - 30) / w, (self.canvas_canvas.height() - 30) / h)
            self.fig.set_dpi(self.fig.get_dpi() * factor)
            self.fig.canvas.draw()

            self.canvas.updateGeometry()
            w, h = self.canvas.get_width_height()
            self.canvas_container.setMinimumSize(w, h)
            self.canvas_container.setMaximumSize(w, h)

            self.canvas_container.move((self.canvas_canvas.width() - w) / 2 + 5,
                                       (self.canvas_canvas.height() - h) / 2 + 5)

            self.updateRuler()
            self.fig.canvas.draw()

        else:
            w, h = self.canvas.get_width_height()
            self.canvas_canvas.setMinimumWidth(w+30)
            self.canvas_canvas.setMinimumHeight(h+30)

            self.canvas_container.move((self.canvas_canvas.width() - w) / 2 + 5, (self.canvas_canvas.height() - h) / 2 + 5)
            self.updateRuler()

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = False

    def scroll_event(self, event):
        if self.control_modifier:
            new_dpi = self.fig.get_dpi() + 10 * event.step

            self.fig.figure_dragger.select_element(None)

            pos = self.fig.transFigure.inverted().transform((event.x, event.y))
            pos_ax = self.fig.transFigure.transform(self.fig.axes[0].get_position())[0]

            self.fig.set_dpi(new_dpi)
            self.fig.canvas.draw()

            self.canvas.updateGeometry()
            w, h = self.canvas.get_width_height()
            self.canvas_container.setMinimumSize(w, h)
            self.canvas_container.setMaximumSize(w, h)

            pos2 = self.fig.transFigure.transform(pos)
            diff = np.array([event.x, event.y]) - pos2

            pos_ax2 = self.fig.transFigure.transform(self.fig.axes[0].get_position())[0]
            diff += pos_ax2 - pos_ax
            self.moveCanvasCanvas(*diff)

            bb = self.fig.axes[0].get_position()

    def updateFigureSize(self):
        w, h = self.canvas.get_width_height()
        self.canvas_container.setMinimumSize(w, h)
        self.canvas_container.setMaximumSize(w, h)

    def changedFigureSize(self, tuple):
        self.fig.set_size_inches(np.array(tuple)/2.54)
        self.fig.canvas.draw()

    def elementSelected(self, element):
        self.input_properties.setElement(element)

    def update(self):
        #self.input_size.setValue(np.array(self.fig.get_size_inches())*2.54)
        self.treeView.deleteEntry(self.fig)
        self.treeView.expand(None)
        self.treeView.expand(self.fig)

        def wrap(func):
            def newfunc(element, event=None):
                self.select_element(element)
                return func(element, event)
            return newfunc
        self.fig.figure_dragger.on_select = wrap(self.fig.figure_dragger.on_select)

        def wrap(func):
            def newfunc(*args):
                self.updateTitle()
                return func(*args)
            return newfunc
        self.fig.change_tracker.addChange = wrap(self.fig.change_tracker.addChange)

        self.fig.change_tracker.save = wrap(self.fig.change_tracker.save)

        self.treeView.setCurrentIndex(self.fig)

    def updateTitle(self):
        if self.fig.change_tracker.saved:
            self.setWindowTitle("Figure %s - Pylustrator" % self.fig.number)
        else:
            self.setWindowTitle("Figure %s* - Pylustrator" % self.fig.number)

    def select_element(self, element):
        if element is None:
            self.treeView.setCurrentIndex(self.fig)
            self.input_properties.setElement(self.fig)
        else:
            self.treeView.setCurrentIndex(element)
            self.input_properties.setElement(element)

    def closeEvent(self, event):
        if not self.fig.change_tracker.saved:
            reply = QtWidgets.QMessageBox.question(self, 'Warning - Pylustrator', 'The figure has not been saved. '
                                                                    'All data will be lost.\nDo you want to save it?',
                                                   QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.Yes)

            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
            if reply == QtWidgets.QMessageBox.Yes:
                self.fig.change_tracker.save()
