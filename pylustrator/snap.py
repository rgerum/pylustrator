#!/usr/bin/env python
# -*- coding: utf-8 -*-
# snap.py

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

from typing import List, Tuple, Optional

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes._subplots import Axes
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Ellipse, FancyArrowPatch
from matplotlib.text import Text

DIR_X0 = 1
DIR_Y0 = 2
DIR_X1 = 4
DIR_Y1 = 8


def checkXLabel(target: Artist):
    """ checks if the target is the xlabel of an axis """
    for axes in target.figure.axes:
        if axes.xaxis.get_label() == target:
            return axes


def checkYLabel(target: Artist):
    """ checks if the target is the ylabel of an axis """
    for axes in target.figure.axes:
        if axes.yaxis.get_label() == target:
            return axes


class TargetWrapper(object):
    """ a wrapper to add unified set and get position methods for any matplotlib artist """
    target = None

    def __init__(self, target: Artist):
        self.target = target
        self.figure = target.figure
        self.do_scale = True
        self.fixed_aspect = False
        # a patch uses the data_transform
        if isinstance(self.target, mpl.patches.Patch):
            self.get_transform = self.target.get_data_transform
        # axes use the figure_transform
        elif isinstance(self.target, Axes):
            # and optionally have a fixed aspect ratio
            if self.target.get_aspect() != "auto" and self.target.get_adjustable() != "datalim":
                self.fixed_aspect = True
            self.get_transform = lambda: self.target.figure.transFigure
        # texts use get_transform
        elif isinstance(self.target, Text):
            if getattr(self.target, "xy", None) is not None:
                self.do_scale = True
            else:
                self.do_scale = False
            if checkXLabel(self.target):
                self.label_factor = self.figure.dpi / 72.0
                if getattr(self.target, "pad_offset", None) is None:
                    self.target.pad_offset = self.target.get_position()[1] - checkXLabel(
                        self.target).xaxis.labelpad * self.label_factor
                self.label_y = self.target.get_position()[1]
            elif checkYLabel(self.target):
                self.label_factor = self.figure.dpi / 72.0
                if getattr(self.target, "pad_offset", None) is None:
                    self.target.pad_offset = self.target.get_position()[0] - checkYLabel(
                        self.target).yaxis.labelpad * self.label_factor
                self.label_x = self.target.get_position()[0]
            self.get_transform = self.target.get_transform
        # the default is to use get_transform
        else:
            self.get_transform = self.target.get_transform
            self.do_scale = False

    def get_positions(self) -> (int, int, int, int):
        """ get the current position of the target Artist """
        points = []
        if isinstance(self.target, Rectangle):
            points.append(self.target.get_xy())
            p2 = (self.target.get_x() + self.target.get_width(), self.target.get_y() + self.target.get_height())
            points.append(p2)
        elif isinstance(self.target, Ellipse):
            c = self.target.center
            w = self.target.width
            h = self.target.height
            points.append((c[0] - w / 2, c[1] - h / 2))
            points.append((c[0] + w / 2, c[1] + h / 2))
        elif isinstance(self.target, FancyArrowPatch):
            points.append(self.target._posA_posB[0])
            points.append(self.target._posA_posB[1])
            points.extend(self.target.get_path().vertices)
        elif isinstance(self.target, Text):
            points.append(self.target.get_position())
            if checkXLabel(self.target):
                points[0] = (points[0][0], self.label_y)
            elif checkYLabel(self.target):
                points[0] = (self.label_x, points[0][1])
            if getattr(self.target, "xy", None) is not None:
                points.append(self.target.xy)
            bbox = self.target.get_bbox_patch()
            if bbox:
                points.append(bbox.get_transform().transform((bbox.get_x(), bbox.get_y())))
                points.append(
                    bbox.get_transform().transform((bbox.get_x() + bbox.get_width(), bbox.get_y() + bbox.get_height())))
            points[-2:] = self.transform_inverted_points(points[-2:])
        elif isinstance(self.target, Axes):
            p1, p2 = np.array(self.target.get_position())
            points.append(p1)
            points.append(p2)
        elif isinstance(self.target, Legend):
            bbox = self.target.get_frame().get_bbox()
            if isinstance(self.target._get_loc(), int):
                # if the legend doesn't have a location yet, use the left bottom corner of the bounding box
                self.target._set_loc(tuple(self.target.axes.transAxes.inverted().transform(tuple([bbox.x0, bbox.y0]))))
            points.append(self.target.axes.transAxes.transform(self.target._get_loc()))
            # add points to span bounding box around the frame
            points.append([bbox.x0, bbox.y0])
            points.append([bbox.x1, bbox.y1])
        return self.transform_points(points)

    def set_positions(self, points: (int, int)):
        """ set the position of the target Artist """
        points = self.transform_inverted_points(points)

        if isinstance(self.target, Rectangle):
            self.target.set_xy(points[0])
            self.target.set_width(points[1][0] - points[0][0])
            self.target.set_height(points[1][1] - points[0][1])
            if self.target.get_label() is None or not self.target.get_label().startswith("_rect"):
                self.figure.change_tracker.addChange(self.target, ".set_xy([%f, %f])" % tuple(self.target.get_xy()))
                self.figure.change_tracker.addChange(self.target, ".set_width(%f)" % self.target.get_width())
                self.figure.change_tracker.addChange(self.target, ".set_height(%f)" % self.target.get_height())
        elif isinstance(self.target, Ellipse):
            self.target.center = np.mean(points, axis=0)
            self.target.width = points[1][0] - points[0][0]
            self.target.height = points[1][1] - points[0][1]
            self.figure.change_tracker.addChange(self.target, ".center = (%f, %f)" % tuple(self.target.center))
            self.figure.change_tracker.addChange(self.target, ".width = %f" % self.target.width)
            self.figure.change_tracker.addChange(self.target, ".height = %f" % self.target.height)
        elif isinstance(self.target, FancyArrowPatch):
            self.target.set_positions(points[0], points[1])
            self.figure.change_tracker.addChange(self.target,
                                                 ".set_positions(%s, %s)" % (tuple(points[0]), tuple(points[1])))
        elif isinstance(self.target, Text):
            if checkXLabel(self.target):
                axes = checkXLabel(self.target)
                axes.xaxis.labelpad = -(points[0][1] - self.target.pad_offset) / self.label_factor
                self.figure.change_tracker.addChange(axes,
                                                     ".xaxis.labelpad = %f" % axes.xaxis.labelpad)

                self.target.set_position(points[0])
                self.label_y = points[0][1]
            elif checkYLabel(self.target):
                axes = checkYLabel(self.target)
                axes.yaxis.labelpad = -(points[0][0] - self.target.pad_offset) / self.label_factor
                self.figure.change_tracker.addChange(axes,
                                                     ".yaxis.labelpad = %f" % axes.yaxis.labelpad)

                self.target.set_position(points[0])
                self.label_x = points[0][0]
            else:
                self.target.set_position(points[0])
                self.figure.change_tracker.addChange(self.target,
                                                     ".set_position([%f, %f])" % self.target.get_position())
                if getattr(self.target, "xy", None) is not None:
                    self.target.xy = points[1]
                    self.figure.change_tracker.addChange(self.target, ".xy = (%f, %f)" % tuple(self.target.xy))
        elif isinstance(self.target, Legend):
            point = self.target.axes.transAxes.inverted().transform(self.transform_inverted_points(points)[0])
            self.target._loc = tuple(point)
            self.figure.change_tracker.addChange(self.target, "._set_loc((%f, %f))" % tuple(point))
        elif isinstance(self.target, Axes):
            position = np.array([points[0], points[1] - points[0]]).flatten()
            if self.fixed_aspect:
                position[3] = position[2] * self.target.get_position().height / self.target.get_position().width
            self.target.set_position(position)
            self.figure.change_tracker.addChange(self.target, ".set_position([%f, %f, %f, %f])" % tuple(
                np.array([points[0], points[1] - points[0]]).flatten()))

    def get_extent(self) -> (int, int, int, int):
        """ get the extend of the target """
        points = np.array(self.get_positions())
        return [np.min(points[:, 0]),
                np.min(points[:, 1]),
                np.max(points[:, 0]),
                np.max(points[:, 1])]

    def transform_points(self, points: (int, int)) -> (int, int):
        """ transform points from the targets local coordinate system to the figure coordinate system """
        transform = self.get_transform()
        return [transform.transform(p) for p in points]

    def transform_inverted_points(self, points: (int, int)) -> (int, int):
        """ transform points from the figure coordinate system to the targets local coordinate system """
        transform = self.get_transform()
        return [transform.inverted().transform(p) for p in points]


class SnapBase(Line2D):
    """ The base class to implement snaps. """

    def __init__(self, ax_source: Artist, ax_target: Artist, edge: int):
        # wrap both object with a TargetWrapper
        self.ax_source = TargetWrapper(ax_source)
        self.ax_target = TargetWrapper(ax_target)
        self.edge = edge
        # initialize a line object for the visualisation of the snap
        Line2D.__init__(self, [], [], transform=None, clip_on=False, lw=1, zorder=100, linestyle="dashed",
                        color="r", marker="o", ms=1, label="_tmp_snap")
        plt.gca().add_artist(self)

    def getPosition(self, target: TargetWrapper):
        """ get the position of a target """
        try:
            return target.get_extent()
        except AttributeError:
            return np.array(target.figure.transFigure.transform(target.get_position())).flatten()

    def getDistance(self, index: int) -> (int, int):
        """ Calculate the distance of the snap to its target """
        return 0, 0

    def checkSnap(self, index: int) -> Optional[float]:
        """ Return the distance to the targets or None """
        distance = self.getDistance(index)
        if abs(distance) < 10:
            return distance
        return None

    def checkSnapActive(self):
        """ Test if the snap condition is fullfilled """
        distance = min([self.getDistance(index) for index in [0, 1]])
        # show the snap if the distance to a target is smaller than 1
        if abs(distance) < 1:
            self.show()
        else:
            self.hide()

    def show(self):
        """ Implements a visualisation of the snap, e.g. lines to indicate what objects are snapped to what """
        pass

    def hide(self):
        """ Hides the visualisation """
        self.set_data((), ())

    def remove(self):
        """ Remove the snap and its visualisation """
        self.hide()
        try:
            self.axes.artists.remove(self)
        except ValueError:
            pass


class SnapSameEdge(SnapBase):
    """ a snap that checks if two objects share an edge """

    def getDistance(self, index: int) -> (int, int):
        """ Calculate the distance of the snap to its target """
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # and return the difference in the target dimension
        return p1[self.edge] - p2[self.edge]

    def show(self):
        """ A visualisation of the snap, e.g. lines to indicate what objects are snapped to what """
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # if the focus edge is x, draw a line along the edge
        if self.edge % 2 == 0:
            self.set_data((p1[self.edge], p1[self.edge], p2[self.edge], p2[self.edge]),
                          (p1[self.edge - 1], p1[self.edge + 1], p2[self.edge - 1], p2[self.edge + 1]))
        # if the focus edge is y
        else:
            self.set_data((p1[self.edge - 1], p1[self.edge - 3], p2[self.edge - 1], p2[self.edge - 3]),
                          (p1[self.edge], p1[self.edge], p2[self.edge], p2[self.edge]))


class SnapSameDimension(SnapBase):
    """ a snap that checks if two objects have the same width or height """

    def getDistance(self, index: int) -> (int, int):
        """ Calculate the distance of the snap to its target """
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # and the difference of the widths (or heights) of the objects
        return (p2[self.edge - 2] - p2[self.edge]) - (p1[self.edge - 2] - p1[self.edge])

    def show(self):
        """ A visualisation of the snap, e.g. lines to indicate what objects are snapped to what """
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # if the focus edge is x, draw a line though the center of each object
        if self.edge % 2 == 0:
            self.set_data((p1[0], p1[2], np.nan, p2[0], p2[2]),
                          (p1[1] * 0.5 + p1[3] * 0.5, p1[1] * 0.5 + p1[3] * 0.5, np.nan, p2[1] * 0.5 + p2[3] * 0.5,
                           p2[1] * 0.5 + p2[3] * 0.5))
        # if the focus edge is y
        else:
            self.set_data((p1[0] * 0.5 + p1[2] * 0.5, p1[0] * 0.5 + p1[2] * 0.5, np.nan, p2[0] * 0.5 + p2[2] * 0.5,
                           p2[0] * 0.5 + p2[2] * 0.5),
                          (p1[1], p1[3], np.nan, p2[1], p2[3]))


class SnapSamePos(SnapBase):
    """ a snap that checks if two objects have the same position """

    def getPosition(self, text: TargetWrapper) -> (int, int):
        # get the position of an object
        return np.array(text.get_transform().transform(text.target.get_position()))

    def getDistance(self, index: int) -> int:
        """ Calculate the distance of the snap to its target """
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # get the distance of the two objects in the target dimension
        return p1[self.edge] - p2[self.edge]

    def show(self):
        """ A visualisation of the snap, e.g. lines to indicate what objects are snapped to what """
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # draw a line connecting the centers of the objects
        self.set_data((p1[0], p2[0]), (p1[1], p2[1]))


class SnapSameBorder(SnapBase):
    """ A snap that checks if tree axes share the space between them """

    def __init__(self, ax_source: Artist, ax_target: Artist, ax_target2: Artist, edge: int):
        super().__init__(ax_source, ax_target, edge)
        self.ax_target2 = ax_target2

    def overlap(self, p1: list, p2: list, dir: int):
        """ Test if two objects have an overlapping x or y region """
        if p1[dir + 2] < p2[dir] or p1[dir] > p2[dir + 2]:
            return False
        return True

    def getBorders(self, p1: list, p2: list):
        borders = []
        for edge in [0, 1]:
            if self.overlap(p1, p2, 1 - edge):
                if p1[edge + 2] < p2[edge]:
                    dist = p2[edge] - p1[edge + 2]
                    borders.append([edge * 2 + 0, dist])
                if p1[edge] > p2[edge + 2]:
                    dist = p1[edge] - p2[edge + 2]
                    borders.append([edge * 2 + 1, dist])
        return np.array(borders)

    def getDistance(self, index: int):
        """ Calculate the distance of the snap to its target """
        # get the positions of all three targets
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        p3 = self.getPosition(self.ax_target2)

        for edge in [index]:
            if not (self.edge & DIR_X1) and not (self.edge & DIR_Y1):
                if p1[edge + 2] < p2[edge]:
                    continue
            if not (self.edge & DIR_X0) and not (self.edge & DIR_Y0):
                if p1[edge] > p2[edge + 2]:
                    continue
            if (p1[edge + 2] < p2[edge] or p1[edge] > p2[edge + 2]) and self.overlap(p1, p2, 1 - edge):
                distances = np.array([p2[edge] - p1[edge + 2], p1[edge] - p2[edge + 2]])
                index1 = np.argmax(distances)
                distance = distances[index1]
                borders = self.getBorders(p2, p3)
                if len(borders):
                    deltas = distance - borders[:, 1]
                    index2 = np.argmin(np.abs(deltas))
                    self.dir2 = borders[index2, 0]
                    self.dir1 = edge * 2 + index1
                    return deltas[index2] * (-1 + 2 * index1)
        return np.inf

    def getConnection(self, p1: list, p2: list, dir: int):
        """ return the coordinates of a line that spans the space between to axes """
        # check which edge (e.g. x, y) and which direction (e.g. if to change the order of p1 and p2)
        edge, order = dir // 2, dir % 2
        # optionally change p1 with p2
        if order == 1:
            p1, p2 = p2, p1
        # if edge is x
        if edge == 0:
            y = np.mean([max(p1[1], p2[1]), min(p1[3], p2[3])])
            return [[p1[2], p2[0], np.nan], [y, y, np.nan]]
        # if edge is y
        x = np.mean([max(p1[0], p2[0]), min(p1[2], p2[2])])
        return [[x, x, np.nan], [p1[3], p2[1], np.nan]]

    def show(self):
        """ A visualisation of the snap, e.g. lines to indicate what objects are snapped to what """
        # get the positions of all three axes
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        p3 = self.getPosition(self.ax_target2)
        # get the
        x1, y1 = self.getConnection(p1, p2, self.dir1)
        x2, y2 = self.getConnection(p2, p3, self.dir2)
        x1.extend(x2)
        y1.extend(y2)
        self.set_data((x1, y1))


class SnapCenterWith(SnapBase):
    """ A snap that checks if a text is centered with an axes """

    def getPosition(self, text: TargetWrapper) -> (int, int):
        """ get the position of the first object """
        return np.array(text.get_transform().transform(text.target.get_position()))

    def getPosition2(self, axes: TargetWrapper) -> int:
        """ get the position of the second object """
        pos = np.array(axes.figure.transFigure.transform(axes.target.get_position()))
        p = pos[0, :]
        p[self.edge] = np.mean(pos, axis=0)[self.edge]
        return p

    def getDistance(self, index: int) -> int:
        """ Calculate the distance of the snap to its target """
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition2(self.ax_target)
        # get the distance of the two objects in the target dimension
        return p1[self.edge] - p2[self.edge]

    def show(self):
        """ A visualisation of the snap, e.g. lines to indicate what objects are snapped to what """
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition2(self.ax_target)
        # draw a line connecting the centers of the objects
        self.set_data((p1[0], p2[0]), (p1[1], p2[1]))


def checkSnaps(snaps: List[SnapBase]) -> (int, int):
    """ get the x and y offsets the snaps suggest """
    result = [0, 0]
    # iterate over x and y
    for index in range(2):
        # find the best snap
        best = np.inf
        for snap in snaps:
            delta = snap.checkSnap(index)
            if delta is not None and abs(delta) < abs(best):
                best = delta
        # if there is a snap suggestion, store it
        if best < np.inf:
            result[index] = best
    # return the best suggestion
    return result


def checkSnapsActive(snaps: List[SnapBase]):
    """ check if snaps are active and show them if yes """
    for snap in snaps:
        snap.checkSnapActive()


def getSnaps(targets: List[TargetWrapper], dir: int, no_height=False) -> List[SnapBase]:
    """ get all snap objects for the target and the direction """
    snaps = []
    targets = [t.target for t in targets]
    for target in targets:
        if isinstance(target, Legend):
            continue
        if isinstance(target, Text):
            if checkXLabel(target):
                snaps.append(SnapCenterWith(target, checkXLabel(target), 0))
            elif checkYLabel(target):
                snaps.append(SnapCenterWith(target, checkYLabel(target), 1))
            for ax in target.figure.axes + [target.figure]:
                for txt in ax.texts:
                    # for other texts
                    if txt in targets or not txt.get_visible():
                        continue
                    # snap to the x and the y coordinate
                    x, y = txt.get_transform().transform(txt.get_position())
                    snaps.append(SnapSamePos(target, txt, 0))
                    snaps.append(SnapSamePos(target, txt, 1))
            continue
        for index, axes in enumerate(target.figure.axes):
            if axes not in targets and axes.get_visible():
                # axes edged
                if dir & DIR_X0:
                    snaps.append(SnapSameEdge(target, axes, 0))
                if dir & DIR_Y0:
                    snaps.append(SnapSameEdge(target, axes, 1))
                if dir & DIR_X1:
                    snaps.append(SnapSameEdge(target, axes, 2))
                if dir & DIR_Y1:
                    snaps.append(SnapSameEdge(target, axes, 3))

                # snap same dimensions
                if not no_height:
                    if dir & DIR_X0:
                        snaps.append(SnapSameDimension(target, axes, 0))
                    if dir & DIR_X1:
                        snaps.append(SnapSameDimension(target, axes, 2))
                    if dir & DIR_Y0:
                        snaps.append(SnapSameDimension(target, axes, 1))
                    if dir & DIR_Y1:
                        snaps.append(SnapSameDimension(target, axes, 3))

                for axes2 in target.figure.axes:
                    if axes2 != axes and axes2 not in targets and axes2.get_visible():
                        snaps.append(SnapSameBorder(target, axes, axes2, dir))
    return snaps
