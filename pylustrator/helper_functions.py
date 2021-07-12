#!/usr/bin/env python
# -*- coding: utf-8 -*-
# helper_functions.py

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

from __future__ import division
import matplotlib.pyplot as plt
from matplotlib.text import Text
import numpy as np
import traceback
from .parse_svg import svgread
from matplotlib.axes._subplots import Axes
from matplotlib.figure import Figure
from .pyjack import replace_all_refs
import os
from typing import Sequence, Union


def fig_text(x: float, y: float, text: str, unit: str = "cm", *args, **kwargs):
    """
    add a text to the figure positioned in cm
    """
    fig = plt.gcf()
    if unit == "cm":
        x = x / 2.54 / fig.get_size_inches()[0]
        y = y / 2.54 / fig.get_size_inches()[1]
    if x < 0:
        x += 1
    if y < 0:
        y += 1
    return fig.text(x, y, text, picker=True, *args, **kwargs)


def add_axes(dim: Sequence, unit: str = "cm", *args, **kwargs):
    """
    add an axes with dimensions specified in cm
    """
    fig = plt.gcf()
    x, y, w, h = dim
    if unit == "cm":
        x = x / 2.54 / fig.get_size_inches()[0]
        y = y / 2.54 / fig.get_size_inches()[1]
        w = w / 2.54 / fig.get_size_inches()[0]
        h = h / 2.54 / fig.get_size_inches()[1]
    if x < 0:
        x += 1
    if y < 0:
        y += 1
    return plt.axes([x, y, w, h], *args, **kwargs)


def add_image(filename: str):
    """ add an image to the current axes """
    plt.imshow(plt.imread(filename))
    plt.xticks([])
    plt.yticks([])


def changeFigureSize(w: float, h: float, cut_from_top: bool = False, cut_from_left: bool = False, fig: Figure = None):
    """ change the figure size to the given dimensions. Optionally define if to remove or add space at the top or bottom
        and left or right.
    """
    if fig is None:
        fig = plt.gcf()
    oldw, oldh = fig.get_size_inches()
    fx = oldw / w
    fy = oldh / h
    for axe in fig.axes:
        box = axe.get_position()
        if cut_from_top:
            if cut_from_left:
                axe.set_position([1 - (1 - box.x0) * fx, box.y0 * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
            else:
                axe.set_position([box.x0 * fx, box.y0 * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
        else:
            if cut_from_left:
                axe.set_position(
                    [1 - (1 - box.x0) * fx, 1 - (1 - box.y0) * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
            else:
                axe.set_position([box.x0 * fx, 1 - (1 - box.y0) * fy, (box.x1 - box.x0) * fx, (box.y1 - box.y0) * fy])
    for text in fig.texts:
        x0, y0 = text.get_position()
        if cut_from_top:
            if cut_from_left:
                text.set_position([1 - (1- x0) * fx, y0 * fy])
            else:
                text.set_position([x0 * fx, y0 * fy])
        else:
            if cut_from_left:
                text.set_position([1 - (1 - x0) * fx, 1 - (1 - y0) * fy])
            else:
                text.set_position([x0 * fx, 1 - (1 - y0) * fy])
    fig.set_size_inches(w, h, forward=True)


def removeContentFromFigure(fig: Figure):
    """ remove axes and text from a figure """
    axes = []
    for ax in fig._axstack.as_list():
        axes.append(ax)
        fig._axstack.remove(ax)
    text = fig.texts
    fig.texts = []
    return axes + text


def addContentToFigure(fig: Figure, axes: Sequence):
    """ add axes and texts to a figure """
    index = len(fig._axstack.as_list())
    for ax in axes:
        if isinstance(ax, Axes):
            try:  # old matplotlib
                fig._axstack.add(index, ax)
            except TypeError:  # newer matplotlib
                fig._axstack.add(ax)
            index += 1
        else:
            fig.texts.append(ax)


def check_label_exists(fig, label):
    for ax in fig.axes:
        if ax.get_label() == label:
            return True
    return False


def get_unique_label(fig1, label_base):
    label = label_base
    for i in range(9999):
        if check_label_exists(fig1, label):
            label = f"{label_base}_{i}"
        else:
            break
    return label


def imShowFullFigure(im: np.ndarray, filename: str, fig1: Figure, dpi: int, label: str):
    """ create a new axes and display an image in this axes """
    from matplotlib import rcParams
    if dpi is None:
        dpi = rcParams['figure.dpi']
    fig1.set_size_inches(im.shape[1] / dpi, im.shape[0] / dpi)
    ax = plt.axes([0, 0, 1, 1], label=label)
    plt.imshow(im, cmap="gray")
    plt.xticks([])
    plt.yticks([])
    for spine in ["left", "right", "top", "bottom"]:
        ax.spines[spine].set_visible(False)


class changeFolder:
    """
    An environment that changes the working directory
    """
    def __init__(self, directory):
        self.directory = directory

    def __enter__(self):
        self.old_dir = os.getcwd()
        if self.directory:
            os.chdir(self.directory)

    def __exit__(self, type, value, traceback):
        os.chdir(self.old_dir)


def loadFigureFromFile(filename: str, figure: Figure = None, offset: list = None, dpi: int = None, cache: bool = False, label: str = ""):
    """
    Add contents to the current figure from the file defined by filename. It can be either a python script defining
    a figure, an image (filename or directly the numpy array), or an svg file.

    See also :ref:`composing`.

    Parameters
    ----------
    filename : str
        The file to load. Can point to a python script file, an image file or an svg file.
    figure : Figure, optional
        The figure where to add the loaded file. Defaults to the current figure.
    offset : list, optional
        The offset where to import the file. The first two parts define the x and y position and the third part defines
        the units to use. Default is "%", a percentage of the current figure size. It can also be "cm" or "in".
    cache : bool, optional
        Whether to try to cache the figure generated from the file. Only for python files. This option is experimental
        and may not be stable.
    """
    from matplotlib import rcParams
    from pylustrator import changeFigureSize
    import pylustrator

    if label == "":
        label = get_unique_label(figure if figure is not None else plt.gcf(), filename)

    # change to the directory of the filename (to execute the code relative to this directory)
    dirname, filename = os.path.split(filename)
    dirname = os.path.abspath(dirname)
    with changeFolder(dirname):
        if dirname:
            os.chdir(dirname)

        # defaults to the current figure
        if figure is None:
            figure = plt.gcf()

        class noShow:
            """
            An environment that prevents the script from calling the plt.show function
            """
            def __enter__(self):
                # store the show function
                self.show = plt.show
                self.dragger = pylustrator.start

                # define an empty function
                def empty(*args, **kwargs):
                    pass

                # set the show function to the empty function
                plt.show = empty
                pylustrator.start = empty

            def __exit__(self, type, value, traceback):
                # restore the old show function
                plt.show = self.show
                pylustrator.start = self.dragger

        class noNewFigures:
            """
            An environment that prevents the script from creating new figures in the figure manager
            """
            def __enter__(self):
                fig = plt.gcf()
                self.fig = plt.figure
                figsize = rcParams['figure.figsize']
                fig.set_size_inches(figsize[0], figsize[1])
                def figure(num=None, figsize=None, *args, **kwargs):
                    fig = plt.gcf()
                    if figsize is not None:
                        fig.set_size_inches(figsize[0], figsize[1], forward=True)
                    return fig
                plt.figure = figure

            def __exit__(self, type, value, traceback):
                from matplotlib.figure import Figure
                from matplotlib.transforms import TransformedBbox, Affine2D
                plt.figure = self.fig

        # get the size of the old figure
        w1, h1 = figure.get_size_inches()
        axes1 = removeContentFromFigure(figure)
        if len(axes1) == 0:
            w1 = 0
            h1 = 0

        # try to load the filename as an image
        try:
            im = plt.imread(filename)
        except OSError:
            im = None

        # if it is an image, just display the image
        if im is not None:
            im = plt.imread(filename)
            imShowFullFigure(im, os.path.split(filename)[1], figure, dpi=dpi, label=label)
        # if the image is a numpy array, just display the array
        elif isinstance(filename, np.ndarray):
            im = filename
            imShowFullFigure(im, str(im.shape), figure, dpi)
        # if it is a svg file, display the svg file
        elif filename.endswith(".svg"):
            svgread(filename)
        # if not, it should be a python script
        else:
            filename = os.path.abspath(filename)
            cache_filename = filename + ".cache.pkl"

            with noNewFigures():
                # prevent the script we want to load from calling show
                with noShow():
                    import pickle
                    if cache and os.path.exists(cache_filename) and os.path.getmtime(cache_filename) > os.path.getmtime(filename):
                        print("loading from cached file", cache_filename)
                        fig2 = pickle.load(open(cache_filename, "rb"))
                        w, h = fig2.get_size_inches()
                        figure.set_size_inches(w, h)

                        str(figure)  # important! (for some reason I don't know)
                        for ax in fig2.axes:
                            fig2.delaxes(ax)
                            figure._axstack.add(figure._make_key(ax), ax)
                            figure.bbox._parents.update(fig2.bbox._parents)
                            figure.dpi_scale_trans._parents.update(fig2.dpi_scale_trans._parents)
                            replace_all_refs(fig2.bbox, figure.bbox)
                            replace_all_refs(fig2.dpi_scale_trans, figure.dpi_scale_trans)
                            replace_all_refs(fig2, figure)
                    else:
                        # execute the file
                        exec(compile(open(filename, "rb").read(), filename, 'exec'), globals())
                        if cache is True:
                            c = figure.canvas
                            figure.canvas = None
                            figure.bbox.pylustrator = True
                            figure.dpi_scale_trans.pylustrator = True
                            pickle.dump(figure, open(cache_filename, 'wb'))

                            figure.canvas = c

        # get the size of the new figure
        w2, h2 = figure.get_size_inches()
        if offset is not None:
            if len(offset) == 2 or offset[2] == "%":
                w2 += w1 * offset[0]
                h2 += h1 * offset[1]
            elif offset[2] == "in":
                w2 += offset[0]
                h2 += offset[1]
            elif offset[2] == "cm":
                w2 += offset[0] / 2.54
                h2 += offset[1] / 2.54
            changeFigureSize(w2, h2, cut_from_top=True, cut_from_left=True, fig=figure)
        w = max(w1, w2)
        h = max(h1, h2)
        changeFigureSize(w, h, fig=figure)
        if len(axes1):
            axes2 = removeContentFromFigure(figure)
            changeFigureSize(w1, h1, fig=figure)
            addContentToFigure(figure, axes1)

            changeFigureSize(w, h, fig=figure)
            addContentToFigure(figure, axes2)


# helper_functions.py
def convertFromPyplot(old, new):

    w, h = old.get_size_inches()
    new.set_size_inches(w, h)

    str(new)  # important! (for some reason I don't know)
    for ax in old.axes:
        old.delaxes(ax)
        new._axstack.add(new._make_key(ax), ax)
        new.bbox._parents.update(old.bbox._parents)
        new.dpi_scale_trans._parents.update(old.dpi_scale_trans._parents)
        replace_all_refs(old.bbox, new.bbox)
        replace_all_refs(old.dpi_scale_trans, new.dpi_scale_trans)
        replace_all_refs(old.canvas, new.canvas)
        replace_all_refs(old, new)


def mark_inset(parent_axes: Axes, inset_axes: Axes, loc1: Union[int, Sequence[int]] = 1, loc2: Union[int, Sequence[int]] = 2, **kwargs):
    """ like the mark_inset function from matplotlib, but loc can also be a tuple """
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxPatch, BboxConnector
    try:
        loc1a, loc1b = loc1
    except:
        loc1a = loc1
        loc1b = loc1
    try:
        loc2a, loc2b = loc2
    except:
        loc2a = loc2
        loc2b = loc2
    rect = TransformedBbox(inset_axes.viewLim, parent_axes.transData)

    pp = BboxPatch(rect, fill=False, **kwargs)
    parent_axes.add_patch(pp)
    pp.set_clip_on(False)

    p1 = BboxConnector(inset_axes.bbox, rect, loc1=loc1a, loc2=loc1b, **kwargs)
    inset_axes.add_patch(p1)
    p1.set_clip_on(False)
    p2 = BboxConnector(inset_axes.bbox, rect, loc1=loc2a, loc2=loc2b, **kwargs)
    inset_axes.add_patch(p2)
    p2.set_clip_on(False)

    return pp, p1, p2


def draw_from_point_to_bbox(parent_axes: Axes, insert_axes: Axes, point: Sequence, loc=1, **kwargs):
    """ add a box connector from a point to an axes """
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxConnector, Bbox
    rect = TransformedBbox(Bbox([point, point]), parent_axes.transData)
    # rect = TransformedBbox(Bbox([[1, 0], [1, 0]]), parent_axes.transData)
    p1 = BboxConnector(rect, insert_axes.bbox, loc, **kwargs)
    parent_axes.add_patch(p1)
    p1.set_clip_on(False)
    return p1


def draw_from_point_to_point(parent_axes: Axes, insert_axes: Axes, point1: Sequence, point2: Sequence, **kwargs):
    """ add a box connector from a point in on axes to a point in another axes """
    from mpl_toolkits.axes_grid1.inset_locator import TransformedBbox, BboxConnector, Bbox
    rect = TransformedBbox(Bbox([point1, point1]), parent_axes.transData)
    rect2 = TransformedBbox(Bbox([point2, point2]), insert_axes.transData)
    # rect = TransformedBbox(Bbox([[1, 0], [1, 0]]), parent_axes.transData)
    loc = 1
    p1 = BboxConnector(rect, rect2, loc, **kwargs)
    parent_axes.add_patch(p1)
    p1.set_clip_on(False)
    return p1


def mark_inset_pos(parent_axes: Axes, inset_axes: Axes, loc1: Union[int, Sequence[int]], loc2: Union[int, Sequence[int]], point: Sequence, **kwargs):
    """ add a box connector where the second axis is shrinked to a point """
    kwargs["lw"] = 0.8
    ax_new = plt.axes(inset_axes.get_position())
    ax_new.set_xlim(point[0], point[0])
    ax_new.set_ylim(point[1], point[1])
    mark_inset(parent_axes, ax_new, loc1, loc2, **kwargs)
    plt.xticks([])
    plt.yticks([])
    ax_new.set_zorder(inset_axes.get_zorder() - 1)


def VoronoiPlot(points: Sequence, values: Sequence, vmin: float = None, vmax:float = None, cmap=None):
    """ plot the voronoi regions of the poins with the given colormap """
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    from scipy.spatial import Voronoi, voronoi_plot_2d
    from matplotlib import cm

    if cmap is None:
        cmap = cm.get_cmap('viridis')

    vor = Voronoi(points)

    # %%
    patches = []
    dist_list = []
    excluded_indices = []
    for index, p in enumerate(points):
        # print(index)
        reg = vor.regions[vor.point_region[index]]
        if -1 in reg:
            # plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)
            excluded_indices.append(index)
            continue
        distances = np.linalg.norm(np.array([vor.vertices[i] for i in reg]) - p, axis=1)
        if np.max(distances) > 2:
            # plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)
            excluded_indices.append(index)
            continue
        region = np.array([vor.vertices[i] for i in reg])
        polygon = Polygon(region, True)
        patches.append(polygon)
        dists = values[index]
        dist_list.append(dists)
        # plt.plot(p[0], p[1], 'ok', alpha=0.3, ms=1)

    p = PatchCollection(patches, cmap=cmap)
    p.set_clim([vmin, vmax])
    p.set_array(np.array(dist_list))
    p.set_linewidth(10)

    plt.gca().add_collection(p)
    plt.xticks([])
    plt.yticks([])
    return p, excluded_indices


def selectRectangle(axes: Axes = None):
    """ add a rectangle selector to the given axes """
    if axes is None:
        axes = plt.gca()

    def onselect(eclick, erelease):
        'eclick and erelease are matplotlib events at press and release'
        print(' startposition : (%f, %f)' % (eclick.xdata, eclick.ydata))
        print(' endposition   : (%f, %f)' % (erelease.xdata, erelease.ydata))
        print(' used button   : ', eclick.button)

    from matplotlib.widgets import RectangleSelector
    rect_selector = RectangleSelector(axes, onselect)
    return rect_selector


def despine(ax: Axes = None, complete: bool = False):
    """ despine the given axes """
    if not ax:
        ax = plt.gca()
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    if complete:
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
    else:
        # Only show ticks on the left and bottom spines
        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')



letter_index = 0
def add_letter(ax: Axes = None, offset: float = 0, offset2: float = 0, letter: str = None):
    """ add a letter indicating which subplot it is to the given figure """
    global letter_index
    from matplotlib.transforms import Affine2D, ScaledTranslation

    # get the axes
    if ax is None:
        ax = plt.gca()

    # get the figure
    fig = ax.figure

    # get the font properties for figure letters
    font = get_letter_font_prop()

    # if no letter is given
    if letter is None:
        # use the letter_format from the font
        letter = font.letter_format
        # and add a letter given the current letter_index
        letter = letter.replace("a", chr(ord("a") + letter_index))
        letter = letter.replace("A", chr(ord("A") + letter_index))
        # increase the letter index
        letter_index += 1

    # add a transform that gives the coordinates relative to the left top corner of the axes in cm
    transform = Affine2D().scale(1 / 2.54, 1 / 2.54) + fig.dpi_scale_trans + ScaledTranslation(0, 1, ax.transAxes)

    # add a text a the given position
    ax.text(-0.5+offset, offset2, letter, fontproperties=font, transform=transform, ha="center", va="bottom", picker=True)


def get_letter_font_prop():
    """ get the properties of the subplot letters to add """
    from matplotlib.font_manager import FontProperties
    font = FontProperties()
    font.set_family("C:\\WINDOWS\\Fonts\\HelveticaNeue-CondensedBold.ttf")
    font.set_weight("heavy")
    font.set_size(10)
    font.letter_format = "a"
    return font


def add_letters(*args, **kwargs):
    """ add a letter indicating which subplot it is to all of the axes of the given figure """
    for ax in plt.gcf().axes:
        add_letter(ax, *args, **kwargs)


def axes_to_grid(axes=None, track_changes=False):
    # get the axes list
    if axes is None:
        fig = plt.gcf()
        axes = fig.axes

    # get width and heights
    width = np.mean([ax.get_position().width for ax in axes])
    height = np.mean([ax.get_position().height for ax in axes])
    dims = [width, height]

    # group the axes to positions on a grid
    pos = [[], []]
    axes_indices = []
    for ax in axes:
        center = np.mean(ax.get_position().get_points(), axis=0)
        new_indices = [0, 0]
        for i in [0, 1]:
            d = np.abs(pos[i] - center[i])
            if len(d) == 0 or np.min(d) > dims[i]/2:
                pos[i].append(center[i])
                new_indices[i] = len(pos[i])-1
            else:
                new_indices[i] = np.argmin(d)
        axes_indices.append(new_indices)
    # sort the indices
    pos = np.array(pos)
    for i in [0, 1]:
        sorted_indices = np.argsort(pos[i], axis=0)
        for indices in axes_indices:
            indices[i] = sorted_indices[indices[i]]

    # the count of plots
    x_count = np.max([i[0] for i in axes_indices])
    y_count = np.max([i[1] for i in axes_indices])

    # extent of the whole plot area
    x_min = np.min([ax.get_position().get_points()[0][0] for ax in axes])
    x_max = np.max([ax.get_position().get_points()[1][0] for ax in axes])
    y_min = np.min([ax.get_position().get_points()[0][1] for ax in axes])
    y_max = np.max([ax.get_position().get_points()[1][1] for ax in axes])

    # the space between plots
    if x_count == 0:
        x_gap = 0
    else:
        x_gap = ((x_max-x_min)-(x_count+1)*width)/x_count
    if y_count == 0:
        y_gap = 0
    else:
        y_gap = ((y_max-y_min)-(y_count+1)*height)/y_count

    # make all the plots the same size and align them on the grid
    for i, ax in enumerate(axes):
        ax.set_position([x_min+axes_indices[i][0] * (width+x_gap),
                        y_min+axes_indices[i][1] * (height + y_gap),
                        width,
                        height,
                        ])
        if track_changes is True:
            ax.figure.change_tracker.addChange(ax, ".set_position([%f, %f, %f, %f])" % (x_min+axes_indices[i][0] * (width+x_gap), y_min+axes_indices[i][1] * (height + y_gap), width, height))

    # make all the plots have the same limits
    xmin = np.min([ax.get_xlim()[0] for ax in axes])
    xmax = np.max([ax.get_xlim()[1] for ax in axes])
    ymin = np.min([ax.get_ylim()[0] for ax in axes])
    ymax = np.max([ax.get_ylim()[1] for ax in axes])
    for ax in axes:
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

    # hide ticks and labels on plots that are not on the left or bottom
    for i, ax in enumerate(axes):
        if axes_indices[i][0] != 0:
            ax.set_ylabel("")
            ax.set_yticklabels([])
            if track_changes is True:
                ax.figure.change_tracker.addChange(ax, ".get_yaxis().get_label().set_text('')")
                ax.figure.change_tracker.addChange(ax, ".set_yticklabels([])")
        if axes_indices[i][1] != 0:
            ax.set_xlabel("")
            ax.set_xticklabels([])
            if track_changes is True:
                ax.figure.change_tracker.addChange(ax, ".get_xaxis().get_label().set_text('')")
                ax.figure.change_tracker.addChange(ax, ".set_xticklabels([])")
        despine(ax)
        if track_changes is True:
            ax.figure.change_tracker.addChange(ax, ".spines['right'].set_visible(False)")
            ax.figure.change_tracker.addChange(ax, ".spines['top'].set_visible(False)")
