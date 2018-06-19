from __future__ import division, print_function
from qtpy import QtCore, QtWidgets, QtGui

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
                        print(stack_item, len(axes.texts), key)
                        keys_for_lines[stack_item.lineno] = key
                        break
            return func(axes, *args, **kwargs)
        return f
    Axes.text = wrap(Axes.text, fig=False, text="New Text")
    Axes.annotate = wrap(Axes.annotate, fig=False, text="New Annotation")

    Figure.text = wrap(Figure.text, fig=True, text="New Text")
    #Figure.annotate = wrap(Figure.annotate, fig=True, text="New Annotation")
    plt.keys_for_lines = keys_for_lines


def show():
    global figures
    # iterate over figures
    for figure in _pylab_helpers.Gcf.figs:
        # get the window
        window = _pylab_helpers.Gcf.figs[figure].canvas.window
        # add dragger
        FigureDragger(_pylab_helpers.Gcf.figs[figure].canvas.figure, [], [], "cm")
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

""" Window """

class DimensionsWidget(QtWidgets.QWidget):
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


class TextWidget(QtWidgets.QWidget):

    def __init__(self, layout, text):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QHBoxLayout(self)
        self.label = QtWidgets.QLabel(text)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.input1 = QtWidgets.QLineEdit()
        self.editingFinished = self.input1.editingFinished
        self.layout.addWidget(self.input1)

    def setLabel(self, text):
        self.label.setLabel(text)

    def setText(self, text):
        self.input1.setText(text)

    def text(self):
        return self.input1.text()


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



class QColorWidget(QtWidgets.QPushButton):
    valueChanged = QtCore.Signal(str)

    def __init__(self, value):
        super(QtWidgets.QPushButton, self).__init__()
        self.clicked.connect(self.OpenDialog)
        # default value for the color
        if value is None:
            value = "#FF0000FF"
        # set the color
        self.setColor(value)

    def OpenDialog(self):
        # get new color from color picker
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*tuple(mpl.colors.to_rgba_array(self.getColor())[0]*255)), self.parent(), "Choose Color")
        # if a color is set, apply it
        if color.isValid():
            color = mpl.colors.to_hex(color.getRgbF())
            self.setColor(color)

    def setColor(self, value):
        # display and save the new color
        self.setStyleSheet("background-color: %s;" % value)
        self.color = value
        self.valueChanged.emit(self.color)

    def getColor(self):
        # return the color
        return self.color


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

        self.button_color = QColorWidget("#000000FF")
        self.button_color.valueChanged.connect(self.changeColor)
        self.layout.addWidget(self.button_color)

        self.layout.addStretch()

        self.font_size = QtWidgets.QSpinBox()
        self.layout.addWidget(self.font_size)
        self.font_size.valueChanged.connect(self.changeFontSize)

        self.label = QtWidgets.QLabel()
        self.label.setPixmap(qta.icon("fa.font").pixmap(16))
        self.layout.addWidget(self.label)

        self.button_delete = QtWidgets.QPushButton(qta.icon("fa.trash"), "")
        self.button_delete.setCheckable(True)
        self.button_delete.clicked.connect(self.delete)
        self.layout.addWidget(self.button_delete)

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
        fig = self.target.figure
        fig.figure_dragger.removeElement(self.target)
        self.target = None
        #self.target.set_visible(False)
        fig.canvas.draw()

    def changeWeight(self, checked):
        if self.target:
            element = self.target
            self.target = None

            element.set_weight("bold" if checked else "normal")
            element.figure.figure_dragger.addChange(element, ".set_weight(\"%s\")" % ("bold" if checked else "normal",))

            self.target = element
            self.target.figure.canvas.draw()

    def changeStyle(self, checked):
        if self.target:
            element = self.target
            self.target = None

            element.set_style("italic" if checked else "normal")
            element.figure.figure_dragger.addChange(element, ".set_style(\"%s\")" % ("italic" if checked else "normal",))

            self.target = element
            self.target.figure.canvas.draw()

    def changeColor(self, color):
        if self.target:
            element = self.target
            self.target = None

            element.set_color(color)
            element.figure.figure_dragger.addChange(element, ".set_color(\"%s\")" % (color,))

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
            element.figure.figure_dragger.addChange(element, ".set_ha(\"%s\")" % align)

            self.target = element
            self.target.figure.canvas.draw()

    def changeFontSize(self, value):
        if self.target:
            self.target.set_fontsize(value)
            self.target.figure.figure_dragger.addChange(self.target, ".set_fontsize(%d)" % value)
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
                entry = entry.parent
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
        return entry.parent

    def getNameOfEntry(self, entry):
        return str(entry)

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
            entry.parent = parent_entry
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


class QItemProperties(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(tuple)
    element = None
    transform = None
    transform_index = 0
    scale_type = 0

    def __init__(self, layout, fig, tree):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.tree = tree

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
        self.input_text.editingFinished.connect(self.changeText)

        self.input_xlabel = TextWidget(self.layout, "X-Label:")
        self.input_xlabel.editingFinished.connect(self.changeXLabel)

        self.input_xlim = DimensionsWidget(self.layout, "X-Lim:", "-", "")
        self.input_xlim.valueChanged.connect(self.changeXLim)

        self.input_ylabel = TextWidget(self.layout, "Y-Label:")
        self.input_ylabel.editingFinished.connect(self.changeYLabel)

        self.input_ylim = DimensionsWidget(self.layout, "Y-Lim:", "-", "")
        self.input_ylim.valueChanged.connect(self.changeYLim)

        self.input_font_properties = TextPropertiesWidget(self.layout)

        self.button_add_text = QtWidgets.QPushButton("add text")
        self.layout.addWidget(self.button_add_text)
        self.button_add_text.clicked.connect(self.buttonAddTextClicked)

        self.button_add_annotation = QtWidgets.QPushButton("add annotation")
        self.layout.addWidget(self.button_add_annotation)
        self.button_add_annotation.clicked.connect(self.buttonAddAnnotationClicked)

        #self.input_xlabel = TextWidget(self.layout, ":")
        #self.input_xlabel.editingFinished.connect(self.changeText)

        #self.radio_buttons[0].setChecked(True)

        self.fig = fig

    def buttonAddTextClicked(self):
        """
        key = getReference(self.element)
        if isinstance(self.element, Axes):
            index = len(self.element.texts)
            key2 = key+".texts[%d].new" % index
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transAxes)
            self.fig.figure_dragger.addChange(key2, key+".text(0.5, 0.5, 'New Text', transform=%s.transAxes)  # id=%s" % (key, key2))
        if isinstance(self.element, Figure):
            index = len(self.element.texts)
            key2 = key + ".texts[%d].new" % index
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transFigure)
            self.fig.figure_dragger.addChange(key2,
                                              key + ".text(0.5, 0.5, 'New Text', transform=%s.transFigure)  # id=%s" % (key, key2))
                                            """
        if isinstance(self.element, Axes):
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transAxes)
            self.fig.figure_dragger.addChange(self.element,
                                              ".text(0.5, 0.5, 'New Text', transform=%s.transAxes)  # id=%s.new" % (
                                              getReference(self.element), getReference(text)), text, ".new")
        if isinstance(self.element, Figure):
            text = self.element.text(0.5, 0.5, "New Text", transform=self.element.transFigure)
            self.fig.figure_dragger.addChange(self.element,
                                              ".text(0.5, 0.5, 'New Text', transform=%s.transFigure)  # id=%s.new" % (
                                              getReference(self.element), getReference(text)), text, ".new")
        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(text)
        self.fig.figure_dragger.select_element(text)
        self.fig.canvas.draw()
        self.setElement(text)
        self.input_text.input1.selectAll()
        self.input_text.input1.setFocus()

    def buttonAddAnnotationClicked(self):
        text = self.element.annotate("New Annotation", (self.element.get_xlim()[0], self.element.get_ylim()[0]), (np.mean(self.element.get_xlim()), np.mean(self.element.get_ylim())), arrowprops=dict(arrowstyle="->"))
        self.fig.figure_dragger.addChange(self.element, ".annotate('New Annotation', %s, %s, arrowprops=dict(arrowstyle='->'))  # id=%s.new" % (text.xy, text.get_position(), getReference(text)),
                                          text, ".new")

        self.tree.updateEntry(self.element, update_children=True)
        self.fig.figure_dragger.make_dragable(text)
        self.fig.figure_dragger.select_element(text)
        self.fig.canvas.draw()
        self.setElement(text)
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

            self.fig.figure_dragger.addChange(self.element, ".set_position([%f, %f, %f, %f])" % (pos.x0, pos.y0, pos.width, pos.height))
        except AttributeError:
            pos = value

            self.fig.figure_dragger.addChange(self.element, ".set_position([%f, %f])" % (pos[0], pos[1]))
        self.element.set_position(pos)
        self.fig.canvas.draw()

    def changeSize(self, value):
        if isinstance(self.element, Figure):

            if self.scale_type == 0:
                self.fig.set_size_inches(value)
                self.fig.figure_dragger.addChange(self.element, ".set_size_inches(%f/2.54, %f/2.54, forward=True)" % (value[0]*2.54, value[1]*2.54))
            else:
                if self.scale_type == 1:
                    changeFigureSize(value[0], value[1], fig=self.fig)
                elif self.scale_type == 2:
                    changeFigureSize(value[0], value[1], cut_from_top=True, cut_from_left=True, fig=self.fig)
                self.fig.figure_dragger.addChange(self.element, ".set_size_inches(%f/2.54, %f/2.54, forward=True)" % (value[0] * 2.54, value[1] * 2.54))
                for axes in self.fig.axes:
                    pos = axes.get_position()
                    self.fig.figure_dragger.addChange(axes, ".set_position([%f, %f, %f, %f])" % (pos.x0, pos.y0, pos.width, pos.height))
                for text in self.fig.texts:
                    pos = text.get_position()
                    self.fig.figure_dragger.addChange(text, ".set_position([%f, %f])" % (pos[0], pos[1]))

            self.fig.canvas.draw()
            self.fig.widget.updateGeometry()
        else:
            pos = self.element.get_position()
            pos.x1 = pos.x0 + value[0]
            pos.y1 = pos.y0 + value[1]
            self.element.set_position(pos)

            self.fig.figure_dragger.addChange(self.element, ".set_position([%f, %f, %f, %f])" % (pos.x0, pos.y0, pos.width, pos.height))

            self.fig.canvas.draw()

    def changeText(self):
        self.element.set_text(self.input_text.text())
        self.fig.figure_dragger.addChange(self.element, ".set_text(\"%s\")" % (self.element.get_text()))
        self.fig.canvas.draw()

    def changeXLabel(self):
        self.element.set_xlabel(self.input_xlabel.text())
        self.fig.figure_dragger.addChange(self.element, ".set_xlabel(\"%s\")" % (self.element.get_xlabel()))
        self.fig.canvas.draw()

    def changeXLim(self):
        self.element.set_xlim(*self.input_xlim.value())
        self.fig.figure_dragger.addChange(self.element, ".set_xlim(%s, %s)" % tuple(str(i) for i in self.element.get_xlim()))
        self.fig.canvas.draw()

    def changeYLabel(self):
        self.element.set_ylabel(self.input_ylabel.text())
        self.fig.figure_dragger.addChange(self.element, ".set_ylabel(\"%s\")" % (self.element.get_ylabel()))
        self.fig.canvas.draw()

    def changeYLim(self):
        self.element.set_ylim(*self.input_ylim.value())
        self.fig.figure_dragger.addChange(self.element, ".set_ylim(%s, %s)" % tuple(str(i) for i in self.element.get_ylim()))
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
        self.input_xlabel.hide()
        self.input_xlim.hide()
        self.input_ylabel.hide()
        self.input_ylim.hide()
        self.button_add_annotation.hide()
        if isinstance(element, Figure):
            pos = element.get_size_inches()
            self.input_shape.setTransform(self.getTransform(element))
            self.input_shape.setValue((pos[0], pos[1]))
            self.input_shape.show()
            self.input_transform.show()
            self.input_shape_transform.show()
            self.button_add_text.show()
        elif isinstance(element, Axes):
            pos = element.get_position()
            self.input_shape.setTransform(self.getTransform(element))
            self.input_shape.setValue((pos.width, pos.height))
            self.input_transform.show()
            self.input_shape.show()
            self.input_xlabel.show()
            self.input_xlabel.setText(element.get_xlabel())
            self.input_xlim.show()
            self.input_xlim.setValue(element.get_xlim())
            self.input_ylabel.show()
            self.input_ylabel.setText(element.get_ylabel())
            self.input_ylim.show()
            self.input_ylim.setValue(element.get_ylim())
            self.button_add_text.show()
            self.button_add_annotation.show()
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
            self.input_text.setText(element.get_text())
            self.input_text.show()
            self.input_font_properties.show()
            self.input_font_properties.setTarget(element)
        except AttributeError:
            self.input_text.hide()
            self.input_font_properties.hide()


class PlotWindow(QtWidgets.QWidget):
    def __init__(self, number, size, *args, **kwargs):
        QtWidgets.QWidget.__init__(self)

        self.canvas = MatplotlibWidget(self, number, size=size)
        self.canvas.window = self
        self.fig = self.canvas.figure
        self.fig.widget = self.canvas

        # widget layout and elements
        self.setWindowTitle("Figure %s" % number)
        self.setWindowIcon(qta.icon("fa.bar-chart"))
        self.layout_main = QtWidgets.QHBoxLayout(self)

        #
        self.layout_tools = QtWidgets.QVBoxLayout()
        self.layout_tools.setContentsMargins(0, 0, 0, 0)
        self.layout_main.addLayout(self.layout_tools)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        widget = QtWidgets.QWidget()
        self.layout_tools.addWidget(widget)
        self.layout_tools = QtWidgets.QVBoxLayout(widget)
        widget.setMaximumWidth(300)
        widget.setMinimumWidth(300)

        self.treeView = MyTreeView(self, self.layout_tools, self.fig)
        self.treeView.item_selected = self.elementSelected

        self.input_properties = QItemProperties(self.layout_tools, self.fig, self.treeView)

        # add plot layout
        self.layout_plot = QtWidgets.QVBoxLayout()
        self.layout_main.addLayout(self.layout_plot)

        # add plot canvas
        self.layout_plot.addWidget(self.canvas)

        # add toolbar
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.layout_plot.addWidget(self.navi_toolbar)
        self.layout_plot.addStretch()

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
        self.fig.figure_dragger.select_element = wrap(self.fig.figure_dragger.select_element)

        def wrap(func):
            def newfunc(*args):
                self.updateTitle()
                return func(*args)
            return newfunc
        self.fig.figure_dragger.addChange = wrap(self.fig.figure_dragger.addChange)

        self.fig.figure_dragger.save = wrap(self.fig.figure_dragger.save)

        self.treeView.setCurrentIndex(self.fig)

    def updateTitle(self):
        if self.fig.figure_dragger.saved:
            self.setWindowTitle("Figure %s" % self.fig.number)
        else:
            self.setWindowTitle("Figure %s*" % self.fig.number)

    def select_element(self, element):
        if element is None:
            self.treeView.setCurrentIndex(self.fig)
            self.input_properties.setElement(self.fig)
        else:
            self.treeView.setCurrentIndex(element)
            self.input_properties.setElement(element)

    def closeEvent(self, event):
        if not self.fig.figure_dragger.saved:
            reply = QtWidgets.QMessageBox.question(self, 'Warning', 'The figure has not been saved. '
                                                                    'All data will be lost.\nDo you want to save it?',
                                                   QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.Yes)

            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
            if reply == QtWidgets.QMessageBox.Yes:
                self.fig.figure_dragger.save()
