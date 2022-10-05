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
import sys
import traceback

from matplotlib import _pylab_helpers

import os
import qtawesome as qta
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from qtpy import QtCore, QtWidgets, QtGui


from .ax_rasterisation import rasterizeAxes, restoreAxes
from .change_tracker import setFigureVariableNames
from .drag_helper import DragManager
from .exception_swallower import swallow_get_exceptions

from .components.qitem_properties import QItemProperties
from .components.tree_view import MyTreeView
from .components.align import Align
from .components.plot_layout import PlotLayout
from .components.info_dialog import InfoDialog
from .components.qpos_and_size import QPosAndSize


def my_excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook

""" Matplotlib overlaod """
figures = {}
app = None
keys_for_lines = {}


def initialize(use_global_variable_names=False, use_exception_silencer=True):
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

    # warning for shell session
    stack_pos = traceback.extract_stack()[-2]
    if not stack_pos.filename.endswith('.py') and not stack_pos.filename.startswith("<ipython-input-"):
        print("WARNING: you are using pylustartor in a shell session. Changes cannot be saved to a file. They will just be printed.", file=sys.stderr)

    setting_use_global_variable_names = use_global_variable_names

    if use_exception_silencer:
        swallow_get_exceptions()

    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    old_pltshow = plt.show
    old_pltfigure = plt.figure
    plt.show = show
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

def pyl_show(hide_window: bool = False):
    """ the function overloads the matplotlib show function.
    It opens a DragManager window instead of the default matplotlib window.
    """
    global figures, app
    # set an application id, so that windows properly stacks them in the task bar
    if sys.platform[:3] == 'win':
        import ctypes
        myappid = 'rgerum.pylustrator'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    # iterate over figures
    window = PlotWindow()
    for figure_number in _pylab_helpers.Gcf.figs.copy():
        fig = _pylab_helpers.Gcf.figs[figure_number].canvas.figure
        window.setFigure(fig)
        window.addFigure(fig)
        # get variable names that point to this figure
        #if setting_use_global_variable_names:
        #    setFigureVariableNames(figure_number)
        # get the window
        #window = _pylab_helpers.Gcf.figs[figure].canvas.window_pylustrator
        # warn about ticks not fitting tick labels
        warnAboutTicks(fig)
        # add dragger
        DragManager(fig)
        window.update()
        # and show it
        if hide_window is False:
            window.show()
    if hide_window is False:
        # execute the application
        app.exec_()


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
        #window = _pylab_helpers.Gcf.figs[figure].canvas.window_pylustrator
        window = PlotWindow()
        window.setFigure(_pylab_helpers.Gcf.figs[figure].canvas.figure)
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


def warnAboutTicks(fig):
    """ warn if the tick labels and tick values do not match, to prevent users from accidently setting wrong tick values """
    import sys
    for index, ax in enumerate(fig.axes):
        ticks = ax.get_yticks()
        labels = [t.get_text() for t in ax.get_yticklabels()]
        for t, l in zip(ticks, labels):
            l = l.replace("−", "-")
            if l == "":
                continue
            try:
                l = float(l)
            except ValueError:
                pass
            # if the label is still a string or too far away from the tick value
            if isinstance(l, str) or abs(t - l) > abs(1e-3 * t):
                ax_name = ax.get_label()
                if ax_name == "":
                    ax_name = "#%d" % index
                else:
                    ax_name = '"' + ax_name + '"'
                print("Warning tick and label differ", t, l, "for axes", ax_name, file=sys.stderr)


""" Window """


class Signals(QtWidgets.QWidget):
    figure_changed = QtCore.Signal(Figure)
    canvas_changed = QtCore.Signal(object)
    figure_size_changed = QtCore.Signal()
    figure_element_selected = QtCore.Signal(object)
    figure_element_child_created = QtCore.Signal(object)


class PlotWindow(QtWidgets.QWidget):
    update_changes_signal = QtCore.Signal(bool, bool, str, str)

    def setFigure(self, figure):
        figure.no_figure_dragger_selection_update = False
        self.fig = figure
        self.signals.figure_changed.emit(figure)

    def setCanvas(self, canvas):
        self.canvas = canvas
        self.canvas.window_pylustrator = self

    def addFigure(self, figure):
        self.figures.append(figure)

        undo_act = QtWidgets.QAction(f"Figure {figure.number}", self)

        def undo():
            self.setFigure(figure)

        undo_act.triggered.connect(undo)
        self.menu_edit.addAction(undo_act)

        #self.preview.addFigure(figure)

    def create_menu(self, layout_parent):
        self.menuBar = QtWidgets.QMenuBar()
        file_menu = self.menuBar.addMenu("&File")

        open_act = QtWidgets.QAction("&Save", self)
        open_act.setShortcut("Ctrl+S")
        open_act.triggered.connect(self.actionSave)
        file_menu.addAction(open_act)

        open_act = QtWidgets.QAction("Save &Image...", self)
        open_act.setShortcut("Ctrl+I")
        open_act.triggered.connect(self.actionSaveImage)
        file_menu.addAction(open_act)

        open_act = QtWidgets.QAction("Exit", self)
        open_act.triggered.connect(self.close)
        open_act.setShortcut("Ctrl+Q")
        file_menu.addAction(open_act)

        file_menu = self.menuBar.addMenu("&Edit")
        self.menu_edit = file_menu

        info_act = QtWidgets.QAction("&Info", self)
        info_act.triggered.connect(self.showInfo)

        self.undo_act = QtWidgets.QAction("Undo", self)
        self.undo_act.triggered.connect(self.undo)
        self.undo_act.setShortcut("Ctrl+Z")
        file_menu.addAction(self.undo_act)

        self.redo_act = QtWidgets.QAction("Redo", self)
        self.redo_act.triggered.connect(self.redo)
        self.redo_act.setShortcut("Ctrl+Y")
        file_menu.addAction(self.redo_act)

        self.menuBar.addAction(info_act)

        layout_parent.addWidget(self.menuBar)

    def undo(self):
        self.fig.figure_dragger.undo()

    def redo(self):
        self.fig.figure_dragger.redo()

    def __init__(self, number: int=0):
        """ The main window of pylustrator

        Args:
            number: the id of the figure
            size: the size of the figure
        """
        super().__init__()

        self.figures = []

        self.signals = Signals()
        self.signals.canvas_changed.connect(self.setCanvas)

        self.plot_layout = PlotLayout(self.signals)

        # widget layout and elements
        self.setWindowTitle("Figure %s - Pylustrator" % number)
        self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "icons", "logo.ico")))
        layout_parent = QtWidgets.QVBoxLayout(self)
        layout_parent.setContentsMargins(0, 0, 0, 0)

        # add the menu
        self.create_menu(layout_parent)

        layout_top_bar = QtWidgets.QHBoxLayout()
        layout_parent.addLayout(layout_top_bar)
        layout_top_bar.setContentsMargins(10, 0, 10, 0)

        button_undo = QtWidgets.QPushButton(qta.icon("mdi.undo"), "")
        button_undo.setToolTip("undo")
        button_undo.clicked.connect(self.undo)
        layout_top_bar.addWidget(button_undo)

        button_redo = QtWidgets.QPushButton(qta.icon("mdi.redo"), "")
        button_redo.setToolTip("redo")
        button_redo.clicked.connect(self.redo)
        layout_top_bar.addWidget(button_redo)

        def updateChangesSignal(undo, redo, undo_text, redo_text):
            button_undo.setDisabled(undo)
            self.undo_act.setDisabled(undo)
            if undo_text != "":
                self.undo_act.setText(f"Undo: {undo_text}")
                button_undo.setToolTip(f"Undo: {undo_text}")
            else:
                self.undo_act.setText(f"Undo")
                button_undo.setToolTip(f"Undo")
            button_redo.setDisabled(redo)
            self.redo_act.setDisabled(redo)
            if redo_text != "":
                self.redo_act.setText(f"Redo: {redo_text}")
                button_redo.setToolTip(f"Redo: {redo_text}")
            else:
                self.redo_act.setText(f"Redo")
                button_redo.setToolTip(f"Redo")

        self.update_changes_signal.connect(updateChangesSignal)

        self.input_size = QPosAndSize(layout_top_bar, self.signals)

        if 0:
            self.layout_main = QtWidgets.QHBoxLayout()
            self.layout_main.setContentsMargins(0, 0, 0, 0)
            layout_parent.addLayout(self.layout_main)
        else:
            self.layout_main = QtWidgets.QSplitter()
            self.layout_main.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            layout_parent.addWidget(self.layout_main)

        #self.preview = FigurePreviews(self)
        #self.layout_main.addWidget(self.preview)
        #
        widget = QtWidgets.QWidget()
        self.layout_tools = QtWidgets.QVBoxLayout(widget)
        widget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        #widget.setMaximumWidth(350)
        #widget.setMinimumWidth(350)
        self.layout_main.addWidget(widget)

        if 0:
            layout_rasterize_buttons = QtWidgets.QHBoxLayout()
            self.layout_tools.addLayout(layout_rasterize_buttons)
            self.button_rasterize = QtWidgets.QPushButton("rasterize")
            layout_rasterize_buttons.addWidget(self.button_rasterize)
            self.button_rasterize.clicked.connect(lambda x: self.rasterize(True))
            self.button_derasterize = QtWidgets.QPushButton("derasterize")
            layout_rasterize_buttons.addWidget(self.button_derasterize)
            self.button_derasterize.clicked.connect(lambda x: self.rasterize(False))
            self.button_derasterize.setDisabled(True)
        elif 0:
            self.button_rasterize = QtWidgets.QAction("rasterize", self)
            self.button_rasterize.triggered.connect(lambda x: self.rasterize(True))
            self.menu_edit.addAction(self.button_rasterize)

            self.button_derasterize = QtWidgets.QAction("derasterize", self)
            self.button_derasterize.triggered.connect(lambda x: self.rasterize(False))
            self.menu_edit.addAction(self.button_derasterize)
            self.button_derasterize.setDisabled(True)

        self.treeView = MyTreeView(self.signals, self.layout_tools)

        self.input_properties = QItemProperties(self.layout_tools, self.signals)
        self.input_align = Align(self.layout_tools, self.signals)

        # add plot layout
        self.layout_main.addWidget(self.plot_layout)

        from .QtGui import ColorChooserWidget
        self.colorWidget = ColorChooserWidget(self, None, self.signals)
        self.colorWidget.setMaximumWidth(150)
        self.layout_main.addWidget(self.colorWidget)

        self.layout_main.setStretchFactor(0, 0)
        self.layout_main.setStretchFactor(1, 1)
        self.layout_main.setStretchFactor(2, 0)

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

    def showEvent(self, event: QtCore.QEvent):
        """ when the window is shown """
        self.colorWidget.updateColors()

    def update(self):
        """ update the tree view """
        # self.input_size.setValue(np.array(self.fig.get_size_inches())*2.54)

        def wrap(func):
            def newfunc(element, event=None):
                self.fig.no_figure_dragger_selection_update = True
                self.signals.figure_element_selected.emit(element)
                ret = func(element, event)
                self.fig.no_figure_dragger_selection_update = False
                return ret

            return newfunc

        self.fig.figure_dragger.on_select = wrap(self.fig.figure_dragger.on_select)
        self.fig.change_tracker.update_changes_signal = self.update_changes_signal
        self.update_changes_signal.emit(True, True, "", "")

        def wrap(func):
            def newfunc(*args):
                self.updateTitle()
                return func(*args)

            return newfunc

        self.fig.change_tracker.addChange = wrap(self.fig.change_tracker.addChange)
        self.fig.change_tracker.save = wrap(self.fig.change_tracker.save)
        self.signals.figure_element_selected.emit(self.fig)

    def updateTitle(self):
        """ update the title of the window to display if it is saved or not """
        if self.fig.change_tracker.saved:
            self.setWindowTitle("Figure %s - Pylustrator" % self.fig.number)
        else:
            self.setWindowTitle("Figure %s* - Pylustrator" % self.fig.number)

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
