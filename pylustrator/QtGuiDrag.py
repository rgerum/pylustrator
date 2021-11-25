#!/usr/bin/env python
# -*- coding: utf-8 -*-
# QtGuiDrag.py

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
from .helper_functions import convertFromPyplot


def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook

""" Matplotlib overlaod """
figures = {}
app = None
keys_for_lines = {}


def initialize(use_global_variable_names=False):
    """
    This will overload the commands ``plt.figure()`` and ``plt.show()``.
    If a figure is created after this command was called (directly or indirectly), a GUI window will be initialized
    that allows to interactively manipulate the figure and generate code in the calling script to define these changes.
    The window will be shown when ``plt.show()`` is called.

    See also :ref:`styling`.

    Parameters
    ---------
    use_global_variable_names : bool, optional
        if used, try to find global variables that reference a figure and use them in the generated code.
    """
    global app, keys_for_lines, old_pltshow, old_pltfigure, setting_use_global_variable_names

    setting_use_global_variable_names = use_global_variable_names

    swallow_get_exceptions()

    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    old_pltshow = plt.show
    old_pltfigure = plt.figure
    plt.show = show
    plt.figure = figure
    patchColormapsWithMetaInfo()

    #stack_call_position = traceback.extract_stack()[-2]
    #stack_call_position.filename

    plt.keys_for_lines = keys_for_lines

    # store the last figure save filename
    sf = Figure.savefig

    def savefig(self, filename, *args, **kwargs):
        self._last_saved_figure = getattr(self, "_last_saved_figure", []) + [(filename, args, kwargs)]
        sf(self, filename, *args, **kwargs)

    Figure.savefig = savefig

    # iterate over figures
    for fig_number in _pylab_helpers.Gcf.figs.copy():
        fig_old = plt.figure(fig_number)
        fig = plt.figure(fig_number, force_add=True)
        convertFromPyplot(fig_old, fig)
        plt.close(fig_old)


def show(hide_window: bool = False):
    """ the function overloads the matplotlib show function.
    It opens a DragManager window instead of the default matplotlib window.
    """
    global figures
    # set an application id, so that windows properly stacks them in the task bar
    if sys.platform[:3] == 'win':
        import ctypes
        myappid = 'rgerum.pylustrator'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # iterate over figures
    for figure in _pylab_helpers.Gcf.figs.copy():
        # get variable names that point to this figure
        if setting_use_global_variable_names:
            setFigureVariableNames(figure)
        # get the window
        window = _pylab_helpers.Gcf.figs[figure].canvas.window_pylustrator
        # warn about ticks not fitting tick labels
        warnAboutTicks(window.fig)
        # add dragger
        DragManager(_pylab_helpers.Gcf.figs[figure].canvas.figure)
        window.update()
        # and show it
        if hide_window is False:
            window.show()
    if hide_window is False:
        # execute the application
        app.exec_()

    plt.show = old_pltshow
    plt.figure = old_pltfigure


class CmapColor(list):
    """ a color like object that has the colormap as metadata """

    def setMeta(self, value, cmap):
        self.value = value
        self.cmap = cmap


def patchColormapsWithMetaInfo():
    """ all colormaps now return color with metadata from which colormap the color came from """
    from matplotlib.colors import Colormap

    cm_call = Colormap.__call__

    def new_call(self, *args, **kwargs):
        c = cm_call(self, *args, **kwargs)
        if isinstance(c, (tuple, list)):
            c = CmapColor(c)
            c.setMeta(args[0], self.name)
        return c

    Colormap.__call__ = new_call


def figure(num=None, figsize=None, force_add=False, *args, **kwargs):
    """ overloads the matplotlib figure call and wrapps the Figure in a PlotWindow """
    global figures
    # if num is not defined create a new number
    if num is None:
        num = len(_pylab_helpers.Gcf.figs) + 1
    # if number is not defined
    if force_add or num not in _pylab_helpers.Gcf.figs.keys():
        # create a new window and store it
        canvas = PlotWindow(num, figsize, *args, **kwargs).canvas
        canvas.figure.number = num
        canvas.figure.clf()
        canvas.manager.num = num
        _pylab_helpers.Gcf.figs[num] = canvas.manager
    # get the canvas of the figure
    manager = _pylab_helpers.Gcf.figs[num]
    # set the size if it is defined
    if figsize is not None:
        _pylab_helpers.Gcf.figs[num].window.setGeometry(100, 100, figsize[0] * 80, figsize[1] * 80)
    # set the figure as the active figure
    _pylab_helpers.Gcf.set_active(manager)
    # return the figure
    return manager.canvas.figure


def warnAboutTicks(fig):
    """ warn if the tick labels and tick values do not match, to prevent users from accidently setting wrong tick values """
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


class myTreeWidgetItem(QtGui.QStandardItem):
    def __init__(self, parent: QtWidgets.QWidget = None):
        """ a tree view item to display the contents of the figure """
        QtGui.QStandardItem.__init__(self, parent)

    def __lt__(self, otherItem: QtGui.QStandardItem):
        """ how to sort the items """
        if self.sort is None:
            return 0
        return self.sort < otherItem.sort


class MyTreeView(QtWidgets.QTreeView):
    item_selected = lambda x, y: 0
    item_clicked = lambda x, y: 0
    item_activated = lambda x, y: 0
    item_hoverEnter = lambda x, y: 0
    item_hoverLeave = lambda x, y: 0

    last_selection = None
    last_hover = None

    def __init__(self, parent: QtWidgets.QWidget, layout: QtWidgets.QLayout, fig: Figure):
        """ A tree view to display the contents of a figure

        Args:
            parent: the parent widget
            layout: the layout to which to add the tree view
            fig: the target figure
        """
        super().__init__()

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

    def selectionChanged(self, selection: QtCore.QItemSelection, y: QtCore.QItemSelection):
        """ when the selection in the tree view changes """
        try:
            entry = selection.indexes()[0].model().itemFromIndex(selection.indexes()[0]).entry
        except IndexError:
            entry = None
        if self.last_selection != entry:
            self.last_selection = entry
            self.item_selected(entry)

    def setCurrentIndex(self, entry: Artist):
        """ set the currently selected entry """
        while entry:
            item = self.getItemFromEntry(entry)
            if item is not None:
                super().setCurrentIndex(item.index())
                return
            try:
                entry = entry.tree_parent
            except AttributeError:
                return

    def treeClicked(self, index: QtCore.QModelIndex):
        """ upon selecting one of the tree elements """
        data = index.model().itemFromIndex(index).entry
        return self.item_clicked(data)

    def treeActivated(self, index: QtCore.QModelIndex):
        """ upon selecting one of the tree elements """
        data = index.model().itemFromIndex(index).entry
        return self.item_activated(data)

    def eventFilter(self, object: QtWidgets.QWidget, event: QtCore.QEvent):
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

    def queryToExpandEntry(self, entry: Artist) -> list:
        """ when expanding a tree item """
        if entry is None:
            return [self.fig]
        return entry.get_children()

    def getParentEntry(self, entry: Artist) -> Artist:
        """ get the parent of an item """
        return entry.tree_parent

    def getNameOfEntry(self, entry: Artist) -> str:
        """ convert an entry to a string """
        try:
            return str(entry)
        except AttributeError:
            return "unknown"

    def getIconOfEntry(self, entry: Artist) -> QtGui.QIcon:
        """ get the icon of an entry """
        if getattr(entry, "_draggable", None):
            if entry._draggable.connected:
                return qta.icon("fa.hand-paper-o")
        return QtGui.QIcon()

    def getEntrySortRole(self, entry: Artist):
        return None

    def getKey(self, entry: Artist) -> Artist:
        """ get the key of an entry, which is the entry itself """
        return entry

    def getItemFromEntry(self, entry: Artist) -> Optional[QtWidgets.QTreeWidgetItem]:
        """ get the tree view item for the given artist """
        if entry is None:
            return None
        key = self.getKey(entry)
        try:
            return self.item_lookup[key]
        except KeyError:
            return None

    def setItemForEntry(self, entry: Artist, item: QtWidgets.QTreeWidgetItem):
        """ store a new artist and tree view widget pair """
        key = self.getKey(entry)
        self.item_lookup[key] = item

    def expand(self, entry: Artist, force_reload: bool = True):
        """ expand the children of a tree view item """
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
                if (isinstance(entry, mpl.spines.Spine) or
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

    def addChild(self, parent_item: QtWidgets.QWidget, entry: Artist, row=None):
        """ add a child to a tree view node """
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
        """ expand a tree view node """
        # Get item and entry
        item = index.model().itemFromIndex(index)
        entry = item.entry
        thread = None

        # Expand
        if item.expanded is False:
            self.expand(entry)
            # thread = Thread(target=self.expand, args=(entry,))

        # Start thread as daemonic
        if thread:
            thread.setDaemon(True)
            thread.start()

    def updateEntry(self, entry: Artist, update_children: bool = False, insert_before: Artist = None, insert_after: Artist = None):
        """ update a tree view node """
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

    def deleteEntry(self, entry: Artist):
        """ delete an entry from the tree """
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
                parent_item.setLabel(name)


class InfoDialog(QtWidgets.QWidget):
    def __init__(self, parent):
        """ A dialog displaying the version number of pylustrator.

        Args:
            parent: the parent widget
        """
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("Pylustrator - Info")
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", "logo.ico")))
        self.layout = QtWidgets.QVBoxLayout(self)

        self.label = QtWidgets.QLabel("")

        pixmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "icons", "logo.png"))
        self.label.setPixmap(pixmap)
        self.label.setMask(pixmap.mask())
        self.layout.addWidget(self.label)

        import pylustrator
        self.label = QtWidgets.QLabel("<b>Version " + pylustrator.__version__ + "</b>")
        font = self.label.font()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.label = QtWidgets.QLabel("Copyright © 2016-2019, Richard Gerum")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.label = QtWidgets.QLabel("<a href=https://pylustrator.readthedocs.io>Documentation</a>")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        self.label.setOpenExternalLinks(True)
        self.layout.addWidget(self.label)


class Align(QtWidgets.QWidget):
    def __init__(self, layout: QtWidgets.QLayout, fig: Figure):
        """ A widget that allows to align the elements of a multi selection.

        Args:
            layout: the layout to which to add the widget
            fig: the target figure
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)
        self.fig = fig

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        actions = ["left_x", "center_x", "right_x", "distribute_x", "top_y", "center_y", "bottom_y", "distribute_y", "group"]
        icons = ["left_x.png", "center_x.png", "right_x.png", "distribute_x.png", "top_y.png", "center_y.png",
                 "bottom_y.png", "distribute_y.png", "group.png"]
        self.buttons = []
        for index, act in enumerate(actions):
            button = QtWidgets.QPushButton(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", icons[index])),
                                           "")
            self.layout.addWidget(button)
            button.clicked.connect(lambda x, act=act: self.execute_action(act))
            self.buttons.append(button)
            if index == 3:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.VLine)
                line.setFrameShadow(QtWidgets.QFrame.Sunken)
                self.layout.addWidget(line)
        self.layout.addStretch()

    def execute_action(self, act: str):
        """ execute an alignment action """
        self.fig.selection.align_points(act)
        self.fig.selection.update_selection_rectangles()
        self.fig.canvas.draw()


class PlotWindow(QtWidgets.QWidget):
    fitted_to_view = False

    def __init__(self, number: int, size: tuple):
        """ The main window of pylustrator

        Args:
            number: the id of the figure
            size: the size of the figure
        """
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
        self.canvas.window_pylustrator = self
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
        layout_parent = QtWidgets.QVBoxLayout(self)

        self.menuBar = QtWidgets.QMenuBar()
        fileMenu = self.menuBar.addMenu("&File")

        openAct = QtWidgets.QAction("&Save", self)
        openAct.setShortcut("Ctrl+S")
        openAct.triggered.connect(self.actionSave)
        fileMenu.addAction(openAct)

        openAct = QtWidgets.QAction("Save &Image...", self)
        openAct.setShortcut("Ctrl+I")
        openAct.triggered.connect(self.actionSaveImage)
        fileMenu.addAction(openAct)

        openAct = QtWidgets.QAction("Exit", self)
        openAct.triggered.connect(self.close)
        openAct.setShortcut("Ctrl+Q")
        fileMenu.addAction(openAct)

        infoAct = QtWidgets.QAction("&Info", self)
        infoAct.triggered.connect(self.showInfo)

        self.menuBar.addAction(infoAct)
        layout_parent.addWidget(self.menuBar)
        layout_parent.setContentsMargins(0, 0, 0, 0)

        self.layout_main = QtWidgets.QHBoxLayout()
        layout_parent.addLayout(self.layout_main)

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

        layout_rasterize_buttons = QtWidgets.QHBoxLayout()
        self.layout_tools.addLayout(layout_rasterize_buttons)
        self.button_rasterize = QtWidgets.QPushButton("rasterize")
        layout_rasterize_buttons.addWidget(self.button_rasterize)
        self.button_rasterize.clicked.connect(lambda x: self.rasterize(True))
        self.button_derasterize = QtWidgets.QPushButton("derasterize")
        layout_rasterize_buttons.addWidget(self.button_derasterize)
        self.button_derasterize.clicked.connect(lambda x: self.rasterize(False))
        self.button_derasterize.setDisabled(True)

        self.treeView = MyTreeView(self, self.layout_tools, self.fig)

        self.no_figure_dragger_selection_update = False
        def item_selected(x):
            self.elementSelected(x)
            if not self.no_figure_dragger_selection_update:
                self.fig.figure_dragger.select_element(x)
        self.treeView.item_selected = item_selected

        self.input_properties = QItemProperties(self.layout_tools, self.fig, self.treeView, self)
        self.input_align = Align(self.layout_tools, self.fig)

        # add plot layout
        self.layout_plot = QtWidgets.QVBoxLayout()
        self.layout_main.addLayout(self.layout_plot)

        # add plot canvas
        self.layout_plot.addWidget(self.canvas_canvas)

        # add toolbar
        self.toolbar = ToolBar(self.canvas, self.fig)
        self.layout_plot.addWidget(self.toolbar)

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

        from .QtGui import ColorChooserWidget
        self.colorWidget = ColorChooserWidget(self, self.canvas)
        self.colorWidget.setMaximumWidth(150)
        self.layout_main.addWidget(self.colorWidget)

    def rasterize(self, rasterize: bool):
        """ convert the figur elements to an image """
        if len(self.fig.selection.targets):
            self.fig.figure_dragger.select_element(None)
        if rasterize:
            rasterizeAxes(self.fig)
            self.button_derasterize.setDisabled(False)
        else:
            restoreAxes(self.fig)
            self.button_derasterize.setDisabled(True)
        self.fig.canvas.draw()

    def actionSave(self):
        """ save the code for the figure """
        self.fig.change_tracker.save()
        for _last_saved_figure, args, kwargs in getattr(self.fig, "_last_saved_figure", []):
            self.fig.savefig(_last_saved_figure, *args, **kwargs)

    def actionSaveImage(self):
        """ save figure as an image """
        path = QtWidgets.QFileDialog.getSaveFileName(self, "Save Image", getattr(self.fig, "_last_saved_figure", [(None,)])[0][0],
                                                     "Images (*.png *.jpg *.pdf)")
        if isinstance(path, tuple):
            path = str(path[0])
        else:
            path = str(path)
        if not path:
            return
        if os.path.splitext(path)[1] == ".pdf":
            self.fig.savefig(path, dpi=300)
        else:
            self.fig.savefig(path)
        print("Saved plot image as", path)

    def showInfo(self):
        """ show the info dialog """
        self.info_dialog = InfoDialog(self)
        self.info_dialog.show()

    def updateRuler(self):
        """ update the ruler around the figure to show the dimensions """
        trans = transforms.Affine2D().scale(1. / 2.54, 1. / 2.54) + self.fig.dpi_scale_trans
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
        end_x = np.ceil(trans.inverted().transform((-offset + w, 0))[0])
        dx = 0.1
        for i, pos_cm in enumerate(np.arange(start_x, end_x, dx)):
            x = (trans.transform((pos_cm, 0))[0] + offset)
            if i % 10 == 0:
                painterX.drawLine(x, l - l1 - 1, x, l - 1)
                text = str("%d" % np.round(pos_cm))
                o = 0
                painterX.drawText(x + 3, o, self.fontMetrics().width(text), o + self.fontMetrics().height(),
                                  QtCore.Qt.AlignLeft,
                                  text)
            elif i % 2 == 0:
                painterX.drawLine(x, l - l2 - 1, x, l - 1)
            else:
                painterX.drawLine(x, l - l3 - 1, x, l - 1)
        painterX.drawLine(0, l - 2, w, l - 2)
        painterX.setPen(QtGui.QPen(QtGui.QColor("white"), 1))
        painterX.drawLine(0, l - 1, w, l - 1)
        self.x_scale.setPixmap(self.pixmapX)
        self.x_scale.setMinimumSize(w, l)
        self.x_scale.setMaximumSize(w, l)

        offset = self.canvas_container.pos().y() + self.canvas_container.height()
        start_y = np.floor(trans.inverted().transform((0, +offset - h))[1])
        end_y = np.ceil(trans.inverted().transform((0, +offset))[1])
        dy = 0.1
        for i, pos_cm in enumerate(np.arange(start_y, end_y, dy)):
            y = (-trans.transform((0, pos_cm))[1] + offset)
            if i % 10 == 0:
                painterY.drawLine(l - l1 - 1, y, l - 1, y)
                text = str("%d" % np.round(pos_cm))
                o = 0
                painterY.drawText(o, y + 3, o + self.fontMetrics().width(text), self.fontMetrics().height(),
                                  QtCore.Qt.AlignRight,
                                  text)
            elif i % 2 == 0:
                painterY.drawLine(l - l2 - 1, y, l - 1, y)
            else:
                painterY.drawLine(l - l3 - 1, y, l - 1, y)
        painterY.drawLine(l - 2, 0, l - 2, h)
        painterY.setPen(QtGui.QPen(QtGui.QColor("white"), 1))
        painterY.drawLine(l - 1, 0, l - 1, h)
        painterY.setPen(QtGui.QPen(QtGui.QColor("#f0f0f0"), 0))
        painterY.setBrush(QtGui.QBrush(QtGui.QColor("#f0f0f0")))
        painterY.drawRect(0, 0, l, l)
        self.y_scale.setPixmap(self.pixmapY)
        self.y_scale.setMinimumSize(l, h)
        self.y_scale.setMaximumSize(l, h)

        w, h = self.canvas.get_width_height()

        self.pixmap = QtGui.QPixmap(w + 100, h + 10)

        self.pixmap.fill(QtGui.QColor("transparent"))

        painter = QtGui.QPainter(self.pixmap)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#666666")))
        painter.drawRect(2, 2, w + 2, h + 2)
        painter.drawRect(0, 0, w + 2, h + 2)

        p = self.canvas_container.pos()
        self.shadow.setPixmap(self.pixmap)
        self.shadow.move(p.x() - 1, p.y() - 1)
        self.shadow.setMinimumSize(w + 100, h + 10)
        self.shadow.setMaximumSize(w + 100, h + 10)

    def showEvent(self, event: QtCore.QEvent):
        """ when the window is shown """
        self.fitToView()
        self.updateRuler()
        self.colorWidget.updateColors()

    def resizeEvent(self, event: QtCore.QEvent):
        """ when the window is resized """
        if self.fitted_to_view:
            self.fitToView(True)
        else:
            self.updateRuler()

    def button_press_event(self, event: QtCore.QEvent):
        """ when a mouse button is pressed """
        if event.button == 2:
            self.drag = np.array([event.x, event.y])

    def mouse_move_event(self, event: QtCore.QEvent):
        """ when the mouse is moved """
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

    def button_release_event(self, event: QtCore.QEvent):
        """ when the mouse button is released """
        if event.button == 2:
            self.drag = None

    def canvas_key_press(self, event: QtCore.QEvent):
        """ when a key in the canvas widget is pressed """
        if event.key == "control":
            self.control_modifier = True

    def canvas_key_release(self, event: QtCore.QEvent):
        """ when a key in the canvas widget is released """
        if event.key == "control":
            self.control_modifier = False

    def moveCanvasCanvas(self, offset_x: float, offset_y: float):
        """ when the canvas is panned """
        p = self.canvas_container.pos()
        self.canvas_container.move(p.x() + offset_x, p.y() + offset_y)

        self.updateRuler()

    def keyPressEvent(self, event: QtCore.QEvent):
        """ when a key is pressed """
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

    def fitToView(self, change_dpi: bool = False):
        """ fit the figure to the view """
        self.fitted_to_view = True
        if change_dpi:
            w, h = self.canvas.get_width_height()
            factor = min((self.canvas_canvas.width() - 30) / w, (self.canvas_canvas.height() - 30) / h)
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
            self.canvas_canvas.setMinimumWidth(w + 30)
            self.canvas_canvas.setMinimumHeight(h + 30)

            self.canvas_container.move((self.canvas_canvas.width() - w) / 2 + 5,
                                       (self.canvas_canvas.height() - h) / 2 + 5)
            self.updateRuler()

    def keyReleaseEvent(self, event: QtCore.QEvent):
        """ when a key is released """
        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = False

    def scroll_event(self, event: QtCore.QEvent):
        """ when the mouse wheel is used to zoom the figure """
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
        """ update the size of the figure """
        w, h = self.canvas.get_width_height()
        self.canvas_container.setMinimumSize(w, h)
        self.canvas_container.setMaximumSize(w, h)

    def changedFigureSize(self, size: tuple):
        """ change the size of the figure """
        self.fig.set_size_inches(np.array(size) / 2.54)
        self.fig.canvas.draw()

    def elementSelected(self, element: Artist):
        """ when an element is selected """
        self.input_properties.setElement(element)

    def update(self):
        """ update the tree view """
        # self.input_size.setValue(np.array(self.fig.get_size_inches())*2.54)
        self.treeView.deleteEntry(self.fig)
        self.treeView.expand(None)
        self.treeView.expand(self.fig)

        def wrap(func):
            def newfunc(element, event=None):
                self.no_figure_dragger_selection_update = True
                self.select_element(element)
                ret = func(element, event)
                self.no_figure_dragger_selection_update = False
                return ret

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
        """ update the title of the window to display if it is saved or not """
        if self.fig.change_tracker.saved:
            self.setWindowTitle("Figure %s - Pylustrator" % self.fig.number)
        else:
            self.setWindowTitle("Figure %s* - Pylustrator" % self.fig.number)

    def select_element(self, element: Artist):
        """ select an element """
        if element is None:
            self.treeView.setCurrentIndex(self.fig)
            self.input_properties.setElement(self.fig)
        else:
            self.treeView.setCurrentIndex(element)
            self.input_properties.setElement(element)

    def closeEvent(self, event: QtCore.QEvent):
        """ when the window is closed, ask the user to save """
        if not self.fig.change_tracker.saved:
            reply = QtWidgets.QMessageBox.question(self, 'Warning - Pylustrator', 'The figure has not been saved. '
                                                                                  'All data will be lost.\nDo you want to save it?',
                                                   QtWidgets.QMessageBox.Cancel | QtWidgets.QMessageBox.No | QtWidgets.QMessageBox.Yes,
                                                   QtWidgets.QMessageBox.Yes)

            if reply == QtWidgets.QMessageBox.Cancel:
                event.ignore()
            if reply == QtWidgets.QMessageBox.Yes:
                self.fig.change_tracker.save()
                # app.clipboard().setText("\r\n".join(output))
