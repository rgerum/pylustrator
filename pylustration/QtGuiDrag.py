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

from .QtShortCuts import AddQColorChoose, QDragableColor
from .drag_bib import FigureDragger

import sys


def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook

""" Matplotlib overlaod """
figures = {}
app = None


def initialize():
    global app
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    plt.show = show
    plt.figure = figure


def show():
    global figures
    # iterate over figures
    for figure in figures:
        # get the window
        window = figures[figure].window
        window.update()
        # and show it
        window.show()
        # add dragger
        FigureDragger(figures[figure].figure, [], [], "cm")
    # execute the application
    app.exec_()


def figure(num=None, size=None, *args, **kwargs):
    global figures
    # if num is not defined create a new number
    if num is None:
        num = len(figures)
    # if number is not defined
    if num not in figures.keys():
        # create a new window and store it
        canvas = PlotWindow(num, *args, **kwargs).canvas
        canvas.figure.number = num
        figures[num] = canvas
    # get the canvas of the figure
    canvas = figures[num]
    # set the size if it is defined
    if size is not None:
        figures[num].window.setGeometry(100, 100, size[0] * 80, size[1] * 80)
    # set the figure as the active figure
    _pylab_helpers.Gcf.set_active(canvas.manager)
    # return the figure
    return canvas.figure

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
        self.input1.valueChanged.connect(self.onValueChanged)
        self.input1.setMaximum(99999)
        self.layout.addWidget(self.input1)

        self.text2 = QtWidgets.QLabel(join)
        self.layout.addWidget(self.text2)

        self.input2 = QtWidgets.QDoubleSpinBox()
        self.input2.setSuffix(" "+unit)
        self.input2.valueChanged.connect(self.onValueChanged)
        self.input2.setMaximum(99999)
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

    def setCheckState(self, state):
        self.noSignal = True
        self.input1.setCheckState(state)
        self.noSignal = False

    def isChecked(self):
        return self.input1.isChecked()


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
        item = self.getItemFromEntry(entry)
        if item is not None:
            super(QtWidgets.QTreeView, self).setCurrentIndex(item.index())

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
        return None
        if isinstance(entry, self.data_file.table_markertype):
            return None
        if isinstance(entry, self.data_file.table_marker):
            if entry.track:
                return entry.track
        return entry.type

    def getNameOfEntry(self, entry):
        return str(entry)
        if isinstance(entry, self.data_file.table_markertype):
            return entry.name
        if isinstance(entry, self.data_file.table_marker):
            return "Marker #%d (frame %d)" % (entry.id, entry.image.sort_index)
        if isinstance(entry, self.data_file.table_line):
            return "Line #%d (frame %d)" % (entry.id, entry.image.sort_index)
        if isinstance(entry, self.data_file.table_rectangle):
            return "Rectangle #%d (frame %d)" % (entry.id, entry.image.sort_index)
        if isinstance(entry, self.data_file.table_track):
            count = entry.track_markers.count()
            if count == 0:
                self.deleteEntry(entry)
                return None
            return "Track #%d (count %d)" % (entry.id, count)
        return "nix"

    def getIconOfEntry(self, entry):
        return QtGui.QIcon()
        if isinstance(entry, self.data_file.table_markertype):
            if entry.mode == TYPE_Normal:
                return qta.icon("fa.crosshairs", color=QtGui.QColor(*HTMLColorToRGB(entry.color)))
            if entry.mode == TYPE_Line:
                return IconFromFile("Line.png", color=QtGui.QColor(*HTMLColorToRGB(entry.color)))
            if entry.mode == TYPE_Rect:
                return IconFromFile("Rectangle.png", color=QtGui.QColor(*HTMLColorToRGB(entry.color)))
            if entry.mode == TYPE_Track:
                return IconFromFile("Track.png", color=QtGui.QColor(*HTMLColorToRGB(entry.color)))
        return QtGui.QIcon()

    def getEntrySortRole(self, entry):
        return None
        if isinstance(entry, self.data_file.table_marker):
            return entry.image.sort_index
        return None

    def getKey(self, entry):
        return type(entry).__name__ + str(entry)  # TODO id

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
            self.addChild(parent_item, entry)

        """
        if parent_item is None:
            # add entry for new type
            self.new_type = self.data_file.table_markertype()
            self.new_type.color = GetColorByIndex(self.data_file.table_markertype.select().count()-1)
            item_type = myTreeWidgetItem("add type")
            item_type.entry = self.new_type
            item_type.setIcon(qta.icon("fa.plus"))
            item_type.setEditable(False)
            self.model.setItem(row + 1, 0, item_type)
            self.setItemForEntry(self.new_type, item_type)
            #self.marker_type_modelitems[-1] = item_type
        """

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

    def __init__(self, layout, fig):
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel()
        self.layout.addWidget(self.label)

        self.input_picker = CheckWidget(self.layout, "Pickable:")
        self.input_picker.stateChanged.connect(self.changePickable)

        self.input_position = DimensionsWidget(self.layout, "Position:", "x", "cm")
        self.input_position.valueChanged.connect(self.changePos)

        self.input_shape = DimensionsWidget(self.layout, "Size:", "x", "cm")
        self.input_shape.valueChanged.connect(self.changeSize)

        self.input_text = TextWidget(self.layout, "Text:")
        self.input_text.editingFinished.connect(self.changeText)

        #self.input_xlabel = TextWidget(self.layout, ":")
        #self.input_xlabel.editingFinished.connect(self.changeText)

        self.fig = fig

    def changePos(self, value):
        pos = self.element.get_position()
        try:
            w, h = pos.width, pos.height
            pos.x0 = value[0]
            pos.y0 = value[1]
            pos.x1 = value[0]+w
            pos.y1 = value[1]+h
        except AttributeError:
            pos = value
        self.element.set_position(pos)
        self.fig.canvas.draw()

    def changeSize(self, value):
        if isinstance(self.element, Figure):
            self.fig.set_size_inches(value)
            self.fig.canvas.draw()
            self.fig.widget.updateGeometry()
        else:
            pos = self.element.get_position()
            pos.x1 = pos.x0 + value[0]
            pos.y1 = pos.y0 + value[1]
            self.element.set_position(pos)
            self.fig.canvas.draw()

    def changeText(self):
        self.element.set_text(self.input_text.text())
        self.fig.canvas.draw()

    def changePickable(self):
        self.element.set_picker(self.input_picker.isChecked())

    def setElement(self, element):
        self.label.setText(str(element))
        self.element = element
        print(repr(element))
        try:
            element._draggable
            print(element.get_picker())
            self.input_picker.setCheckState(element.pickable())
            self.input_picker.show()
        except AttributeError:
            self.input_picker.hide()

        if isinstance(element, Figure):
            pos = element.get_size_inches()
            self.input_shape.setTransform(transforms.Affine2D().scale(2.54, 2.54))
            self.input_shape.setValue((pos[0], pos[1]))
            self.input_shape.show()
        elif isinstance(element, Axes):
            pos = element.get_position()
            self.input_shape.setTransform(transforms.Affine2D().scale(2.54, 2.54) + element.figure.dpi_scale_trans.inverted() + element.figure.transFigure)
            self.input_shape.setValue((pos.width, pos.height))
            self.input_shape.show()
        else:
            self.input_shape.hide()

        try:
            pos = element.get_position()
            if isinstance(element, Axes):
                self.input_position.setTransform(transforms.Affine2D().scale(2.54,
                                                                          2.54) + element.figure.dpi_scale_trans.inverted() + element.figure.transFigure)
            else:
                self.input_position.setTransform(transforms.Affine2D().scale(2.54, 2.54) + element.figure.dpi_scale_trans.inverted() + element.get_transform())
            try:
                self.input_position.setValue(pos)
            except Exception as err:
                print(err)
                self.input_position.setValue((pos.x0, pos.y0))
            self.input_position.show()
        except:
            self.input_position.hide()

        try:
            self.input_text.setText(element.get_text())
            self.input_text.show()
        except AttributeError:
            self.input_text.hide()


class PlotWindow(QtWidgets.QWidget):
    def __init__(self, number, *args, **kwargs):
        QtWidgets.QWidget.__init__(self)

        self.canvas = MatplotlibWidget(self)
        self.canvas.window = self
        self.fig = self.canvas.figure
        self.fig.widget = self.canvas

        # widget layout and elements
        self.setWindowTitle("Figure %s" % number)
        self.setWindowIcon(qta.icon("fa.bar-chart"))
        self.layout_main = QtWidgets.QHBoxLayout(self)

        #
        self.layout_tools = QtWidgets.QVBoxLayout()
        self.layout_main.addLayout(self.layout_tools)

        self.treeView = MyTreeView(self, self.layout_tools, self.fig)
        self.treeView.item_selected = self.elementSelected

        self.input_properties = QItemProperties(self.layout_tools, self.fig)

        # add plot layout
        self.layout_plot = QtWidgets.QVBoxLayout()
        self.layout_main.addLayout(self.layout_plot)

        # add plot canvas

        self.layout_plot.addWidget(self.canvas)
        _pylab_helpers.Gcf.set_active(self.canvas.manager)

        # add toolbar
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.layout_plot.addWidget(self.navi_toolbar)
        self.layout_plot.addStretch()

    def changedFigureSize(self, tuple):
        print("figure changed", tuple)
        self.fig.set_size_inches(np.array(tuple)/2.54)
        self.fig.canvas.draw()

    def elementSelected(self, element):
        print(element)
        self.input_properties.setElement(element)

    def update(self):
        #self.input_size.setValue(np.array(self.fig.get_size_inches())*2.54)
        self.treeView.deleteEntry(self.fig)
        self.treeView.expand(None)
