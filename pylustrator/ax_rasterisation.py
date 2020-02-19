#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ax_rasterisation.py

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

import io
import matplotlib.pyplot as plt
from matplotlib.axes._subplots import Axes
from matplotlib.figure import Figure
from typing import List

from .helper_functions import removeContentFromFigure, addContentToFigure


def stashElements(ax: Axes, names: List[str]):
    """ remove elements from a figure and store them"""
    for attribute in names:
        element = getattr(ax, attribute)
        setattr(ax, "pylustrator_" + attribute, element)
        setattr(ax, attribute, [] if isinstance(element, list) else None)


def popStashedElements(ax: Axes, names: List[str]):
    """ add elements to a figure that were previously removed from it """
    for attribute in names:
        element_list = getattr(ax, attribute)
        if isinstance(element_list, list):
            if getattr(ax, "pylustrator_" + attribute, None) is not None:
                element_list += getattr(ax, "pylustrator_" + attribute)
        else:
            element_list = getattr(ax, "pylustrator_" + attribute)
        setattr(ax, attribute, element_list)
        setattr(ax, "pylustrator_" + attribute, None)


def rasterizeAxes(fig: Figure):
    """ replace contents of a figure with a rasterized image of it """
    restoreAxes(fig)

    parts = removeContentFromFigure(fig)
    for ax in parts:
        stashElements(ax, ["texts", "legend_"])

        if not isinstance(ax, Axes):
            continue
        removeContentFromFigure(fig)
        addContentToFigure(fig, [ax])

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        im = plt.imread(buf)
        buf.close()

        bbox = ax.get_position()
        sx = im.shape[1]
        sy = im.shape[0]
        x1, x2 = int(bbox.x0*sx+1), int(bbox.x1*sx-1)
        y2, y1 = sy-int(bbox.y0*sy+1), sy-int(bbox.y1*sy-1)
        im2 = im[y1:y2, x1:x2]
        stashElements(ax, ["lines", "images", "patches"])

        sx2 = ax.get_xlim()[1] - ax.get_xlim()[0]
        sy2 = ax.get_ylim()[1] - ax.get_ylim()[0]

        x1_offset = 1/sx/bbox.width*sx2
        x2_offset = 1/sx/bbox.width*sx2
        y1_offset = 1 / sy / bbox.height * sy2
        y2_offset = 1 / sy / bbox.height * sy2

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        ax.pylustrator_rasterized = ax.imshow(im2, extent=[ax.get_xlim()[0]+x1_offset, ax.get_xlim()[1]-x2_offset-x1_offset,
                                                           ax.get_ylim()[0]+y1_offset, ax.get_ylim()[1]-y2_offset-y1_offset], aspect="auto")
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)

        popStashedElements(ax, ["texts", "legend_"])
    removeContentFromFigure(fig)
    addContentToFigure(fig, parts)


def restoreAxes(fig: Figure):
    """ restore contents of a figure """
    list_axes = fig.axes
    for ax in list_axes:
        im = getattr(ax, "pylustrator_rasterized", None)
        if im is not None:
            try:
                im.remove()
            except ValueError:
                pass
            del im
        popStashedElements(ax, ["lines", "texts", "images", "patches"])
