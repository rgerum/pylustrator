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

from typing import TYPE_CHECKING, List, Optional, Tuple, Any, Sequence, cast
from packaging import version
from numpy.typing import NDArray

if TYPE_CHECKING:
    from PyQt5 import QtCore, QtGui, QtWidgets
else:
    from qtpy import QtCore, QtGui, QtWidgets

import matplotlib as mpl
import numpy as np
from matplotlib.artist import Artist

try:  # starting from mpl version 3.6.0
    from matplotlib.axes import Axes
except ImportError:
    from matplotlib.axes._subplots import Axes  # ty:ignore[unresolved-import]
from matplotlib.legend import Legend
from matplotlib.patches import Patch, Rectangle, Ellipse, FancyArrowPatch
from matplotlib.text import Text
from matplotlib.figure import Figure

from matplotlib.figure import SubFigure  # since matplotlib 3.4.0
from .helper_functions import main_figure

# Type alias for a 2D point - internally always a numpy array
Point = NDArray[np.floating[Any]]
PointList = List[Point]


def _to_point(p: Tuple[float, float] | Sequence[float] | NDArray[Any]) -> Point:
    """Convert any point-like input to our internal Point representation (numpy array)."""
    return np.asarray(p, dtype=np.float64)


def _to_tuple(p: Point) -> Tuple[float, float]:
    """Convert internal Point to tuple for matplotlib API calls."""
    return (float(p[0]), float(p[1]))


DIR_X0 = 1
DIR_Y0 = 2
DIR_X1 = 4
DIR_Y1 = 8


def checkXLabel(target: Artist):
    """checks if the target is the xlabel of an axis"""
    for axes in target.figure.axes:
        if axes.xaxis.get_label() == target:
            return axes


def checkYLabel(target: Artist):
    """checks if the target is the ylabel of an axis"""
    for axes in target.figure.axes:
        if axes.yaxis.get_label() == target:
            return axes


def cache_property(object, name):
    if getattr(object, f"_pylustrator_cached_{name}", False) is True:
        return
    setattr(object, f"_pylustrator_cached_{name}", True)
    getter = getattr(object, f"get_{name}")
    setter = getattr(object, f"set_{name}")

    def new_getter(*args, **kwargs):
        if getattr(object, f"_pylustrator_cache_{name}", None) is None:
            setattr(object, f"_pylustrator_cache_{name}", getter(*args, **kwargs))
        return getattr(object, f"_pylustrator_cache_{name}", None)

    def new_setter(*args, **kwargs):
        result = setter(*args, **kwargs)
        setattr(object, f"_pylustrator_cache_{name}", None)
        return result

    setattr(object, f"get_{name}", new_getter)
    setattr(object, f"set_{name}", new_setter)


class TargetWrapper(object):
    """a wrapper to add unified set and get position methods for any matplotlib artist"""

    def __init__(self, target: Artist):
        self.target: Artist = target
        figure = target.figure
        if figure is None or not isinstance(figure, Figure):
            raise ValueError("TargetWrapper needs a figure")
        self.figure: Figure = figure
        self.do_scale = True
        self.fixed_aspect = False
        # a patch uses the data_transform
        if isinstance(self.target, Patch):
            self.get_transform = self.target.get_data_transform
        # axes use the figure_transform
        elif isinstance(self.target, Axes):
            # and optionally have a fixed aspect ratio
            if (
                    self.target.get_aspect() != "auto"
                    and self.target.get_adjustable() != "datalim"
            ):
                self.fixed_aspect = True
            # old matplotlib version
            if version.parse(mpl.__version__) < version.parse("3.4.0"):
                self.get_transform = lambda: self.target.figure.transFigure
            else:
                self.get_transform = (
                    lambda: self.target.figure.transSubfigure
                    if isinstance(self.target.figure, SubFigure)
                    else self.target.figure.transFigure
                )

            # cache the get_position
            cache_property(self.target, "position")
        # texts use get_transform
        elif isinstance(self.target, Text):
            if getattr(self.target, "xy", None) is not None:
                self.do_scale = True
            else:
                self.do_scale = False
            if checkXLabel(self.target):
                self.label_factor = self.figure.dpi / 72.0
                if getattr(self.target, "pad_offset", None) is None:
                    self.target.pad_offset = (
                            self.target.get_position()[1]
                            - checkXLabel(self.target).xaxis.labelpad * self.label_factor
                    )
                self.label_y = self.target.get_position()[1]
            elif checkYLabel(self.target):
                self.label_factor = self.figure.dpi / 72.0
                if getattr(self.target, "pad_offset", None) is None:
                    self.target.pad_offset = (
                            self.target.get_position()[0]
                            - checkYLabel(self.target).yaxis.labelpad * self.label_factor
                    )
                self.label_x = self.target.get_position()[0]
            self.get_transform = self.target.get_transform
        # the default is to use get_transform
        else:
            self.get_transform = self.target.get_transform
            self.do_scale = False

    def get_positions(
            self, use_previous_offset: bool = False, update_offset: bool = False
    ) -> PointList:
        """get the current position of the target Artist"""
        points: PointList = []
        if isinstance(self.target, Rectangle):
            points.append(_to_point(self.target.get_xy()))
            p2 = (
                self.target.get_x() + self.target.get_width(),
                self.target.get_y() + self.target.get_height(),
            )
            points.append(_to_point(p2))
        elif isinstance(self.target, Ellipse):
            c = cast(Tuple[float, float], self.target.center)
            w = self.target.width
            h = self.target.height
            points.append(_to_point((c[0] - w / 2, c[1] - h / 2)))
            points.append(_to_point((c[0] + w / 2, c[1] + h / 2)))
        elif isinstance(self.target, FancyArrowPatch):
            points.append(_to_point(self.target._posA_posB[0]))  # ty:ignore[unresolved-attribute]
            points.append(_to_point(self.target._posA_posB[1]))  # ty:ignore[unresolved-attribute]
            for vertex in self.target.get_path().vertices:
                points.append(_to_point(vertex))
        elif isinstance(self.target, Text):
            points.append(_to_point(self.target.get_position()))
            if checkXLabel(self.target):
                points[0] = _to_point((points[0][0], self.label_y))
            elif checkYLabel(self.target):
                points[0] = _to_point((self.label_x, points[0][1]))
            if getattr(self.target, "xy", None) is not None:
                points.append(_to_point(self.target.xy))  # ty:ignore[unresolved-attribute]
            bbox = self.target.get_bbox_patch()
            if bbox:
                points.append(
                    _to_point(
                        bbox.get_transform().transform((bbox.get_x(), bbox.get_y()))
                    )
                )
                points.append(
                    _to_point(
                        bbox.get_transform().transform(
                            (
                                bbox.get_x() + bbox.get_width(),
                                bbox.get_y() + bbox.get_height(),
                            )
                        )
                    )
                )
            points[-2:] = self.transform_inverted_points(points[-2:])
            if use_previous_offset is True:
                offset = getattr(self.target, "_pylustrator_offset", _to_point((0, 0)))
                points[2] = points[0] + offset + points[2] - points[1]
                points[1] = points[0] + offset
            else:
                if (
                        getattr(self.target, "_pylustrator_offset", None) is None
                        or update_offset
                ):
                    self.target._pylustrator_offset = points[1] - points[0]  # ty:ignore[invalid-assignment]
        elif isinstance(self.target, Axes):
            p1, p2 = np.array(self.target.get_position())
            points.append(_to_point(p1))
            points.append(_to_point(p2))
        elif isinstance(self.target, SubFigure):
            points.append(_to_point((self.target.bbox.x0, self.target.bbox.y0)))
            points.append(_to_point((self.target.bbox.x1, self.target.bbox.y1)))
        elif isinstance(self.target, Legend):
            bbox = self.target.get_frame().get_bbox()
            if isinstance(self.target.axes, Axes):
                transform = self.target.axes.transAxes
            elif isinstance(self.target.figure, Figure):
                transform = self.target.figure.transFigure
            else:
                transform = self.target.figure.transSubfigure
            if isinstance(self.target._get_loc(), int):
                # if the legend doesn't have a location yet, use the left bottom corner of the bounding box
                self.target._set_loc(
                    tuple(transform.inverted().transform(tuple([bbox.x0, bbox.y0])))
                )
            points.append(_to_point(transform.transform(self.target._get_loc())))
            # add points to span bounding box around the frame
            points.append(_to_point((bbox.x0, bbox.y0)))
            points.append(_to_point((bbox.x1, bbox.y1)))
            if use_previous_offset is True:
                offset = getattr(self.target, "_pylustrator_offset", _to_point((0, 0)))
                points[2] = points[0] + offset + points[2] - points[1]
                points[1] = points[0] + offset
            else:
                if (
                        getattr(self.target, "_pylustrator_offset", None) is None
                        or update_offset
                ):
                    self.target._pylustrator_offset = points[1] - points[0]
        return self.transform_points(points)

    def set_positions(self, points: Sequence[Point]) -> None:
        """set the position of the target Artist"""
        pts = self.transform_inverted_points(points)

        if self.figure.figure is not None:
            change_tracker = self.figure.figure.change_tracker
        else:
            change_tracker = self.figure.change_tracker

        if isinstance(self.target, Rectangle):
            self.target.set_xy(_to_tuple(pts[0]))
            self.target.set_width(float(pts[1][0] - pts[0][0]))
            self.target.set_height(float(pts[1][1] - pts[0][1]))
            label = self.target.get_label()
            if not isinstance(label, str):
                raise TypeError("Label is not a string")
            if label is None or not label.startswith("_rect"):
                change_tracker.addChange(
                    self.target, ".set_xy([%f, %f])" % tuple(self.target.get_xy())
                )
                change_tracker.addChange(
                    self.target, ".set_width(%f)" % self.target.get_width()
                )
                change_tracker.addChange(
                    self.target, ".set_height(%f)" % self.target.get_height()
                )
        elif isinstance(self.target, Ellipse):
            self.target.center = _to_tuple(np.mean(pts, axis=0))
            self.target.width = float(pts[1][0] - pts[0][0])
            self.target.height = float(pts[1][1] - pts[0][1])
            change_tracker.addChange(
                self.target,
                ".center = (%f, %f)" % self.target.center,
            )
            change_tracker.addChange(self.target, ".width = %f" % self.target.width)
            change_tracker.addChange(self.target, ".height = %f" % self.target.height)
        elif isinstance(self.target, FancyArrowPatch):
            self.target.set_positions(_to_tuple(pts[0]), _to_tuple(pts[1]))
            change_tracker.addChange(
                self.target,
                ".set_positions(%s, %s)" % (_to_tuple(pts[0]), _to_tuple(pts[1])),
            )
        elif isinstance(self.target, Text):
            if checkXLabel(self.target):
                axes = checkXLabel(self.target)
                axes.xaxis.labelpad = (
                        -(pts[0][1] - self.target.pad_offset) / self.label_factor  # ty:ignore[unresolved-attribute]
                )
                change_tracker.addChange(
                    axes, ".xaxis.labelpad = %f" % axes.xaxis.labelpad
                )

                self.target.set_position(_to_tuple(pts[0]))
                self.label_y = float(pts[0][1])
            elif checkYLabel(self.target):
                axes = checkYLabel(self.target)
                axes.yaxis.labelpad = (
                        -(pts[0][0] - self.target.pad_offset) / self.label_factor  # ty:ignore[unresolved-attribute]
                )
                change_tracker.addChange(
                    axes, ".yaxis.labelpad = %f" % axes.yaxis.labelpad
                )

                self.target.set_position(_to_tuple(pts[0]))
                self.label_x = float(pts[0][0])
            else:
                self.target.set_position(_to_tuple(pts[0]))
                if isinstance(self.target, Text):
                    change_tracker.addNewTextChange(self.target)
                else:
                    change_tracker.addChange(
                        self.target,
                        ".set_position([%f, %f])" % self.target.get_position(),
                    )
                if getattr(self.target, "xy", None) is not None:
                    self.target.xy = _to_tuple(pts[1])  # ty:ignore[invalid-assignment]
                    change_tracker.addChange(
                        self.target,
                        ".xy = (%f, %f)" % self.target.xy,  # ty:ignore[unresolved-attribute]
                    )
        elif isinstance(self.target, Legend):
            if isinstance(self.target.axes, Axes):
                transform = self.target.axes.transAxes
            elif isinstance(self.target.figure, Figure):
                transform = self.target.figure.transFigure
            else:
                transform = self.target.figure.transSubfigure
            point = transform.inverted().transform(pts[0])
            self.target._loc = tuple(point)  # ty:ignore[invalid-assignment]
            change_tracker.addNewLegendChange(self.target)
            # change_tracker.addChange(self.target, "._set_loc((%f, %f))" % tuple(point))
        elif isinstance(self.target, Axes):
            position = np.array([pts[0], pts[1] - pts[0]]).flatten()
            if self.fixed_aspect:
                position[3] = (
                        position[2]
                        * self.target.get_position().height
                        / self.target.get_position().width
                )
            self.target.set_position(position)
            change_tracker.addNewAxesChange(self.target)
            # change_tracker.addChange(self.target, ".set_position([%f, %f, %f, %f])" % tuple(
            #    np.array([pts[0], pts[1] - pts[0]]).flatten()))
        setattr(self.target, "_pylustrator_cached_get_extend", None)

    def get_extent(self) -> Tuple[float, float, float, float]:
        # get get_extent as it can be called very frequently when checking snap conditions
        if getattr(self.target, "_pylustrator_cached_get_extend_added", False):
            setattr(self.target, "_pylustrator_cached_get_extend_added", True)
        if getattr(self.target, "_pylustrator_cached_get_extend", None) is None:
            setattr(self.target, "_pylustrator_cached_get_extend", self.do_get_extent())
        return getattr(self.target, "_pylustrator_cached_get_extend")

    def do_get_extent(self) -> Tuple[float, float, float, float]:
        """get the extent of the target"""
        points = np.array(self.get_positions())
        return (
            np.min(points[:, 0]),
            np.min(points[:, 1]),
            np.max(points[:, 0]),
            np.max(points[:, 1]),
        )

    def transform_points(self, points: Sequence[Point]) -> PointList:
        """transform points from the targets local coordinate system to the figure coordinate system"""
        transform = self.get_transform()
        return [_to_point(transform.transform(p)) for p in points]

    def transform_inverted_points(self, points: Sequence[Point]) -> PointList:
        """transform points from the figure coordinate system to the targets local coordinate system"""
        transform = self.get_transform()
        return [_to_point(transform.inverted().transform(p)) for p in points]


class SnapBase:
    """The base class to implement snaps."""

    data = None

    def __init__(self, ax_source: Artist, ax_target: Artist, edge: int):
        # wrap both object with a TargetWrapper
        self.ax_source = TargetWrapper(ax_source)
        self.ax_target = TargetWrapper(ax_target)
        self.edge = edge
        # initialize a line object for the visualisation of the snap
        self.draw_path = QtWidgets.QGraphicsPathItem()
        parent = main_figure(ax_source)._pyl_graphics_scene_snapparent
        parent.scene().addItem(self.draw_path)
        pen1 = QtGui.QPen(QtGui.QColor("red"), 2)
        pen1.setStyle(QtCore.Qt.PenStyle.DashLine)
        self.draw_path.setPen(pen1)

    def getPosition(self, target: TargetWrapper) -> Tuple[float, float, float, float]:
        """get the position of a target"""
        try:
            return target.get_extent()
        except AttributeError:
            pos = target.figure.transFigure.transform(
                cast(Any, target.target).get_position()
            )
            x, y = float(pos[0]), float(pos[1])
            return (x, y, x, y)

    def getDistance(self, index: int) -> float:
        """Calculate the distance of the snap to its target"""
        return 0.0

    def checkSnap(self, index: int) -> Optional[float]:
        """Return the distance to the targets or None"""
        distance = self.getDistance(index)
        if abs(distance) < 10:
            return distance
        return None

    def checkSnapActive(self):
        """Test if the snap condition is fullfilled"""
        distance = min([self.getDistance(index) for index in [0, 1]])
        # show the snap if the distance to a target is smaller than 1
        if abs(distance) < 1:
            self.show()
        else:
            self.hide()

    def show(self):
        """Implements a visualisation of the snap, e.g. lines to indicate what objects are snapped to what"""
        pass

    def set_data(self, xdata, ydata):
        painter_path = QtGui.QPainterPath()
        move = True
        current_pos = (0, 0)
        for x, y in zip(xdata, ydata):
            if np.isnan(x):
                move = True
                continue
            y = self.ax_target.figure.canvas.height() - y
            if move is True:
                painter_path.moveTo(x, y)
                current_pos = (x, y)
                move = False
            else:
                if current_pos[0] > x:
                    painter_path.moveTo(x, y)
                    painter_path.lineTo(*current_pos)
                    current_pos = (x, y)
                else:
                    painter_path.lineTo(x, y)
                    current_pos = (x, y)
        self.draw_path.setPath(painter_path)
        self.data = (xdata, ydata)

    def hide(self):
        """Hides the visualisation"""
        self.set_data((), ())

    def remove(self):
        """Remove the snap and its visualisation"""
        self.hide()

        scene = self.draw_path.scene()
        if scene is None:
            return
        scene.removeItem(self.draw_path)


class SnapSameEdge(SnapBase):
    """a snap that checks if two objects share an edge"""

    def getDistance(self, index: int) -> float:
        """Calculate the distance of the snap to its target"""
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # and return the difference in the target dimension
        return float(p1[self.edge] - p2[self.edge])

    def show(self):
        """A visualisation of the snap, e.g. lines to indicate what objects are snapped to what"""
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # if the focus edge is x, draw a line along the edge
        if self.edge % 2 == 0:
            self.set_data(
                (p1[self.edge], p1[self.edge], p2[self.edge], p2[self.edge]),
                (
                    p1[self.edge - 1],
                    p1[self.edge + 1],
                    p2[self.edge - 1],
                    p2[self.edge + 1],
                ),
            )
        # if the focus edge is y
        else:
            self.set_data(
                (
                    p1[self.edge - 1],
                    p1[self.edge - 3],
                    p2[self.edge - 1],
                    p2[self.edge - 3],
                ),
                (p1[self.edge], p1[self.edge], p2[self.edge], p2[self.edge]),
            )


class SnapSameDimension(SnapBase):
    """a snap that checks if two objects have the same width or height"""

    def getDistance(self, index: int) -> float:
        """Calculate the distance of the snap to its target"""
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # and the difference of the widths (or heights) of the objects
        return float(
            (p2[self.edge - 2] - p2[self.edge]) - (p1[self.edge - 2] - p1[self.edge])
        )

    def show(self):
        """A visualisation of the snap, e.g. lines to indicate what objects are snapped to what"""
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # if the focus edge is x, draw a line though the center of each object
        if self.edge % 2 == 0:
            self.set_data(
                (p1[0], p1[2], np.nan, p2[0], p2[2]),
                (
                    p1[1] * 0.5 + p1[3] * 0.5,
                    p1[1] * 0.5 + p1[3] * 0.5,
                    np.nan,
                    p2[1] * 0.5 + p2[3] * 0.5,
                    p2[1] * 0.5 + p2[3] * 0.5,
                ),
            )
        # if the focus edge is y
        else:
            self.set_data(
                (
                    p1[0] * 0.5 + p1[2] * 0.5,
                    p1[0] * 0.5 + p1[2] * 0.5,
                    np.nan,
                    p2[0] * 0.5 + p2[2] * 0.5,
                    p2[0] * 0.5 + p2[2] * 0.5,
                ),
                (p1[1], p1[3], np.nan, p2[1], p2[3]),
            )


class SnapSamePos(SnapBase):
    """a snap that checks if two objects have the same position"""

    def getPosition(self, target: TargetWrapper) -> Tuple[float, float, float, float]:
        # get the position of an object
        if not isinstance(target.target, Text):
            raise ValueError("SnapSamePos can only be used with text")
        pos = target.get_transform().transform(target.target.get_position())
        x, y = float(pos[0]), float(pos[1])
        return (x, y, x, y)

    def getDistance(self, index: int) -> float:
        """Calculate the distance of the snap to its target"""
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # get the distance of the two objects in the target dimension
        return float(p1[self.edge] - p2[self.edge])

    def show(self):
        """A visualization of the snap, e.g. lines to indicate what objects are snapped to what"""
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        # draw a line connecting the centers of the objects
        self.set_data((p1[0], p2[0]), (p1[1], p2[1]))


class SnapSameBorder(SnapBase):
    """A snap that checks if tree axes share the space between them"""

    def __init__(
            self, ax_source: Artist, ax_target: Artist, ax_target2: Artist, edge: int
    ):
        super().__init__(ax_source, ax_target, edge)
        self.ax_target2 = TargetWrapper(ax_target2)

    def overlap(
            self,
            p1: Tuple[float, float, float, float],
            p2: Tuple[float, float, float, float],
            dir: int,
    ):
        """Test if two objects have an overlapping x or y region"""
        if p1[dir + 2] < p2[dir] or p1[dir] > p2[dir + 2]:
            return False
        return True

    def getBorders(
            self,
            p1: Tuple[float, float, float, float],
            p2: Tuple[float, float, float, float],
    ):
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
        """Calculate the distance of the snap to its target"""
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
            if (p1[edge + 2] < p2[edge] or p1[edge] > p2[edge + 2]) and self.overlap(
                    p1,
                    p2,
                    1 - edge,
            ):
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

    def getConnection(self, p1: Tuple[float, float, float, float],
                      p2: Tuple[float, float, float, float], dir: int):
        """return the coordinates of a line that spans the space between to axes"""
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
        """A visualisation of the snap, e.g. lines to indicate what objects are snapped to what"""
        # get the positions of all three axes
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition(self.ax_target)
        p3 = self.getPosition(self.ax_target2)
        # get the
        x1, y1 = self.getConnection(p1, p2, self.dir1)
        x2, y2 = self.getConnection(p2, p3, self.dir2)
        x1.extend(x2)
        y1.extend(y2)
        self.set_data(x1, y1)


class SnapCenterWith(SnapBase):
    """A snap that checks if a text is centered with an axes"""

    def getPosition(self, target: TargetWrapper) -> Tuple[float, float, float, float]:
        """get the position of the first object"""
        target_text = target.target
        if not isinstance(target_text, Text):
            raise ValueError("SnapCenterWith can only be used with axes")
        return np.array(target.get_transform().transform(target_text.get_position()))

    def getPosition2(self, axes: TargetWrapper) -> np.ndarray:
        """get the position of the second object"""
        target_axes = axes.target
        if not isinstance(target_axes, Axes):
            raise ValueError("SnapCenterWith can only be used with axes")
        pos = np.array(axes.figure.transFigure.transform(target_axes.get_position()))
        p = pos[0, :]
        p[self.edge] = np.mean(pos, axis=0)[self.edge]
        return p

    def getDistance(self, index: int) -> float:
        """Calculate the distance of the snap to its target"""
        # only if the right edge index (x or y) is queried, if not the distance is infinite
        if self.edge % 2 != index:
            return np.inf
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition2(self.ax_target)
        # get the distance of the two objects in the target dimension
        return float(p1[self.edge] - p2[self.edge])

    def show(self):
        """A visualisation of the snap, e.g. lines to indicate what objects are snapped to what"""
        # get the position of both objects
        p1 = self.getPosition(self.ax_source)
        p2 = self.getPosition2(self.ax_target)
        # draw a line connecting the centers of the objects
        self.set_data((p1[0], p2[0]), (p1[1], p2[1]))


def checkSnaps(snaps: List[SnapBase]) -> list[float]:
    """get the x and y offsets the snaps suggest"""
    result: list[float] = [0, 0]
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
    """check if snaps are active and show them if yes"""
    for snap in snaps:
        snap.checkSnapActive()


def getSnaps(targets: List[TargetWrapper], dir: int, no_height=False) -> List[SnapBase]:
    """get all snap objects for the target and the direction"""
    snaps = []
    target_artists: List[Artist] = [t.target for t in targets]
    for target in target_artists:
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
                    if txt in target_artists or not txt.get_visible():
                        continue
                    # snap to the x and the y coordinate
                    x, y = txt.get_transform().transform(txt.get_position())
                    snaps.append(SnapSamePos(target, txt, 0))
                    snaps.append(SnapSamePos(target, txt, 1))
            continue
        for index, axes in enumerate(target.figure.axes):
            if axes not in target_artists and axes.get_visible():
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
                    if (
                            axes2 != axes
                            and axes2 not in target_artists
                            and axes2.get_visible()
                    ):
                        snaps.append(SnapSameBorder(target, axes, axes2, dir))
    return snaps
