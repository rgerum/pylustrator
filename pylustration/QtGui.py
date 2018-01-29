from __future__ import division, print_function
from qtpy import QtCore, QtWidgets, QtGui

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
from .matplotlibwidget import MatplotlibWidget
from matplotlib import _pylab_helpers
import matplotlib as mpl
import qtawesome as qta

from .QtShortCuts import AddQColorChoose, QDragableColor

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
        # update the colors
        window.updateColors()
        # and show it
        window.show()
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

""" Figure list functions """


def addChildren(color_artists, parent):
    for artist in parent.get_children():
        # ignore empty texts
        if isinstance(artist, mpl.text.Text) and artist.get_text() == "":
            continue

        # add the children of the item (not for text or ticks)
        if not isinstance(artist, (mpl.text.Text, mpl.axis.XTick, mpl.axis.YTick)):
            addChildren(color_artists, artist)

        # iterate over the elements
        for color_type_name in ["edgecolor", "facecolor", "color"]:
            colors = getattr(artist, "get_" + color_type_name, lambda: None)()
            # ignore colors that are not set
            if colors is None:
                continue
            # test if it is a colormap
            try:
                cmap = colors.cmap
                value = colors.value
            except AttributeError:
                cmap = None

            # convert to array
            if not (isinstance(colors, np.ndarray) and len(colors.shape) > 1):
                colors = [colors]

            # omit blacks and whites
            if mpl.colors.to_hex(colors[0]) == "#000000" or mpl.colors.to_hex(colors[0]) == "#ffffff":
                continue

            # if we have a colormap
            if cmap:
                # iterate over the colors of the colormap
                for index, color in enumerate(cmap.get_color()):
                    # convert to hex
                    color = mpl.colors.to_hex(color)
                    # check if it is already in the dictionary
                    if color not in color_artists:
                        color_artists[color] = []
                    # add the artist
                    color_artists[color].append([color_type_name, artist, value, cmap, index])
            else:
                # iterate over the colors
                for color in colors:
                    # ignore transparent colors
                    if mpl.colors.to_rgba(color)[3] == 0:
                        continue
                    # convert to hey
                    color = mpl.colors.to_hex(color)
                    # check if it is already in the dictionary
                    if color not in color_artists:
                        color_artists[color] = []
                    # add the artist
                    color_artists[color].append([color_type_name, artist, None, None, None])

def figureListColors(figure):
    figure.color_artists = {}
    addChildren(figure.color_artists, figure)

def figureSwapColor(figure, new_color, color_base):
    if getattr(figure, "color_artists", None) is None:
        figureListColors(figure)
    for data in figure.color_artists[color_base]:
        # get the data
        color_type_name, artist, value, cmap, index = data
        # if the color is part of a colormap, update the colormap
        if cmap:
            # update colormap
            cmap.set_color(new_color, index)
            # use the attributes setter method
            getattr(artist, "set_" + color_type_name)(cmap(value))
        else:
            # use the attributes setter method
            getattr(artist, "set_" + color_type_name)(new_color)

""" Window """


class PlotWindow(QtWidgets.QWidget):
    def __init__(self, number, *args, **kwargs):
        QtWidgets.QWidget.__init__(self)

        # widget layout and elements
        self.setWindowTitle("Figure %s" % number)
        self.setWindowIcon(qta.icon("fa.bar-chart"))
        self.layout_main = QtWidgets.QHBoxLayout(self)

        # add plot layout
        self.layout_plot = QtWidgets.QVBoxLayout(self)
        self.layout_main.addLayout(self.layout_plot)

        # add plot canvas
        self.canvas = MatplotlibWidget(self)
        self.canvas.window = self
        self.layout_plot.addWidget(self.canvas)
        _pylab_helpers.Gcf.set_active(self.canvas.manager)

        # add toolbar
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.layout_plot.addWidget(self.navi_toolbar)
        self.layout_plot.addStretch()

        # initialize color artist dict
        self.color_artists = {}

        # add color chooser layout
        self.layout_right = QtWidgets.QVBoxLayout()
        self.layout_colors = QtWidgets.QVBoxLayout()
        self.layout_right.addLayout(self.layout_colors)
        self.layout_colors2 = QtWidgets.QVBoxLayout()
        self.layout_right.addLayout(self.layout_colors2)
        self.layout_main.addLayout(self.layout_right)



    def addColorButton(self, color, basecolor=None):
        button = QDragableColor(mpl.colors.to_hex(color))
        self.layout_colors.addWidget(button)
        button.color_changed.connect(lambda c, color_base=basecolor: self.color_selected(c, color_base))
        if basecolor:
            self.color_buttons[basecolor] = button
        self.color_buttons_list.append(button)

    def updateColors(self):
        # add recursively all artists of the figure
        figureListColors(self.canvas.figure)
        self.color_artists = self.canvas.figure.color_artists

        # iterate over all colors
        self.color_buttons = {}
        self.color_buttons_list = []

        for color in self.color_artists:
            self.addColorButton(color, color)

        # add a text widget to allow easy copy and paste
        self.colors_text_widget = QtWidgets.QTextEdit()
        self.colors_text_widget.setAcceptRichText(False)
        self.layout_colors2.addWidget(self.colors_text_widget)
        self.colors_text_widget.setText("\n".join([mpl.colors.to_hex(color) for color in self.color_artists]))
        self.colors_text_widget.textChanged.connect(self.colors_changed)

        # update the canvas dimensions
        self.canvas.updateGeometry()

    def colors_changed(self):
        # when the colors in the text edit changed
        for index, color in enumerate(self.colors_text_widget.toPlainText().split("\n")):
            try:
                color = mpl.colors.to_hex(color.strip())
            except ValueError:
                continue
            if len(self.color_buttons_list) <= index:
                self.addColorButton(color)
            self.color_buttons_list[index].setColor(color)

    def color_selected(self, new_color, color_base):
        if color_base is None:
            return
        figureSwapColor(self.canvas.figure, new_color, color_base)
        # redraw the plot
        self.canvas.draw()
