#!/usr/bin/env python
# -*- coding: utf-8 -*-
# lab_colormap.py

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

""" Colormap """
import numpy as np
from typing import Sequence, Union
from matplotlib.colors import Colormap, ListedColormap, to_rgb


class CmapColor(list):
    """ a class that appends metadate to a color """
    def setMeta(self, value, cmap):
        self.value = value
        self.cmap = cmap


def convert_rgb2lab(colors: Sequence):
    """ convert colors from rgb to lab color space """
    from skimage.color import rgb2lab
    return [rgb2lab(np.array(c)[None, None, :3]) for c in colors]


def convert_lab2rgb(colors):
    """ convert colors from lab to rgb color space """
    from skimage.color import lab2rgb
    return [lab2rgb(np.array(c))[0, 0, :3] for c in colors]


class LabColormap(ListedColormap):
    """ a custom colormap that blends between N custom colors """
    init_colors = None

    def __init__(self, colors: Sequence, N: int, stops=None):
        """ initialize with the given colors and stops """
        # store stops
        self.stops = stops
        # set colors
        self.set_color(colors)
        # initialize
        Colormap.__init__(self, "test", N)

    def _init(self):
        """ generate the colormap from the given colors (used by ListedColormap) """
        # convert to lab
        lab_colors = convert_rgb2lab(self.init_colors)
        # initialize new list
        colors = []
        # iterate over stops
        stops = self.get_stops()
        for j in range(len(self.init_colors) - 1):
            # interpolate between stops in lab
            for i in np.linspace(stops[j], stops[j + 1], int(self.N / (len(stops) - 1))):
                colors.append(lab_colors[j] * (1 - i) + i * lab_colors[j + 1])
        # convert back to rgb
        self.colors = convert_lab2rgb(colors)
        # initialize a listed colormap
        ListedColormap._init(self)

    def __call__(self, value: float, *args, **kwargs):
        """ get the color associated with the given value from the colormap """
        # get the color
        result = Colormap.__call__(self, value, *args, **kwargs)
        # add meta values to it
        result = CmapColor(result)
        result.setMeta(value, self)
        # return the color
        return result

    def get_color(self) -> Sequence:
        """ return all the colors """
        # return the colors
        return self.init_colors

    def set_color(self, color: Union[str, Sequence], index: int = None):
        """ set a color to the given index """
        # update the color according to the index
        if index is not None:
            self.init_colors[index] = to_rgb(color)
        # or update the whole list
        else:
            # ensure that the colors are rgb
            self.init_colors = [to_rgb(c) for c in color]
        # linearize the lightness
        self.linearize_lightness()
        # notify that we have to reinitialize the colormap
        self._isinit = False

    def get_stops(self) -> Sequence:
        """ return the stops """
        # get the stops
        stops = self.stops
        # if they are not defined, interpolate from 0 to 1
        if stops is None:
            stops = np.linspace(0, 1, len(self.init_colors))
        # return the stops
        return stops

    def linearize_lightness(self):
        """ linearize the lightness of the colors in the colormap """
        # convert to lab
        lab_colors = convert_rgb2lab(self.init_colors)
        # define start and end lightness
        lightness_start = lab_colors[0][0, 0, 0]
        lichtness_end = lab_colors[-1][0, 0, 0]
        # iterate over stops
        stops = self.get_stops()
        for j in range(1, len(stops) - 1):
            # interpolate lightness value
            lab_colors[j][0, 0, 0] = lightness_start * (1 - stops[j]) + stops[j] * lichtness_end
        # convert back to rgb
        self.init_colors = convert_lab2rgb(lab_colors)
