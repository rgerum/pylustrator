#!/usr/bin/env python
# -*- coding: utf-8 -*-
# drag_helper.py

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

import numpy as np
from matplotlib.artist import Artist
from matplotlib.figure import Figure, SubFigure
from matplotlib.axes import Axes
from matplotlib.text import Text
from matplotlib.patches import Rectangle
from matplotlib.backend_bases import MouseEvent, KeyEvent, Event
from typing import TYPE_CHECKING, Sequence, Callable, Tuple, List, Any, cast, Type

if TYPE_CHECKING:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from .components.plot_layout import GraphicsRectItemWithView
else:
    from qtpy import QtCore, QtGui, QtWidgets

from .snap import TargetWrapper, getSnaps, checkSnaps, checkSnapsActive, SnapBase
from .change_tracker import ChangeTracker
from pylustrator.change_tracker import UndoRedo
import time

DIR_X0 = 1
DIR_Y0 = 2
DIR_X1 = 4
DIR_Y1 = 8

blit = False


class GrabFunctions(object):
    """basic functionality used by all grabbers"""

    figure: Figure
    target = None
    dir: int
    snaps: list[SnapBase]
    targets: list[TargetWrapper]

    got_artist = False

    def __init__(self, parent, dir: int, no_height=False):
        figure: Figure = parent.figure
        if not isinstance(figure, Figure):
            raise TypeError()
        self.figure = figure
        self.parent = parent
        self.dir = dir
        self.snaps = []
        self.no_height = no_height

    def on_motion(self, evt: Event):
        """callback when the object is moved"""
        if not isinstance(evt, MouseEvent):
            raise TypeError()
        if self.got_artist:
            self.movedEvent(evt)
            self.moved = True

    def button_press_event(self, evt: MouseEvent):
        """when the mouse is pressed"""
        self.got_artist = True
        self.moved = False

        self._c1 = self.figure.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.clickedEvent(evt)

    def button_release_event(self, event: MouseEvent):
        """when the mouse is released"""
        if self.got_artist:
            self.got_artist = False
            self.figure.canvas.mpl_disconnect(self._c1)
            self.releasedEvent(event)

    def clickedEvent(self, event: MouseEvent):
        """when the mouse is clicked"""
        self.parent.start_move()
        self.mouse_xy = (event.x, event.y)

        for s in self.snaps:
            s.remove()
        self.snaps = []

        self.snaps = getSnaps(self.targets, self.dir, no_height=self.no_height)

        if blit is True:
            for target in self.targets:
                target.target.set_animated(True)

            self.figure.canvas.draw()
            self.bg = self.figure.canvas.copy_from_bbox(self.figure.bbox)
        else:
            pass
        self.time = time.time()

    def releasedEvent(self, event: MouseEvent):
        """when the mouse is released"""
        for snap in self.snaps:
            snap.remove()
        self.snaps = []

        self.parent.end_move()

        if blit is True:
            for target in self.targets:
                target.target.set_animated(False)
        else:
            pass

    def movedEvent(self, event: MouseEvent):
        """when the mouse is moved"""
        if len(self.targets) == 0:
            return

        dx = event.x - self.mouse_xy[0]
        dy = event.y - self.mouse_xy[1]

        keep_aspect = (
            "control" in event.key.split("+") if event.key is not None else False
        )
        ignore_snaps = (
            "shift" in event.key.split("+") if event.key is not None else False
        )

        self.parent.move(
            [dx, dy],
            self.dir,
            self.snaps,
            keep_aspect_ratio=keep_aspect,
            ignore_snaps=ignore_snaps,
        )

        if blit is True:
            fig = self.figure
            fig.canvas.restore_region(self.bg)
            for target in self.targets:
                fig.draw_artist(target.target)
            # copy the image to the GUI state, but screen might not be changed yet
            fig.canvas.blit(fig.bbox)
            # flush any pending GUI events, re-painting the screen if needed
            fig.canvas.flush_events()
        else:
            self.figure.canvas.schedule_draw()


class GrabbableRectangleSelection(GrabFunctions):
    grabbers: list["GrabberGeneric"]

    def addGrabber(
        self, x: float, y: float, dir: int, GrabberClass: Type["GrabberGeneric"]
    ):
        # add a grabber object at the given coordinates
        self.grabbers.append(GrabberClass(self, x, y, dir, self.graphics_scene))

    def __init__(self, figure: Figure, graphics_scene: "GraphicsRectItemWithView"):
        self.grabbers = []
        pos = [0, 0, 0, 0]
        self.positions = np.array(pos, dtype=float)
        self.p1 = self.positions[:2]
        self.p2 = self.positions[2:]
        self.figure = figure
        self.graphics_scene = graphics_scene
        self.graphics_scene_myparent = QtWidgets.QGraphicsRectItem(
            0, 0, 0, 0, self.graphics_scene
        )
        self.graphics_scene_snapparent = QtWidgets.QGraphicsRectItem(
            0, 0, 0, 0, self.graphics_scene
        )
        figure._pyl_graphics_scene_snapparent = self.graphics_scene_snapparent

        GrabFunctions.__init__(
            self, self, DIR_X0 | DIR_X1 | DIR_Y0 | DIR_Y1, no_height=True
        )

        self.addGrabber(0, 0, DIR_X0 | DIR_Y0, GrabberGenericRound)
        self.addGrabber(0.5, 0, DIR_Y0, GrabberGenericRectangle)
        self.addGrabber(1, 1, DIR_X1 | DIR_Y1, GrabberGenericRound)
        self.addGrabber(1, 0.5, DIR_X1, GrabberGenericRectangle)
        self.addGrabber(0, 1, DIR_X0 | DIR_Y1, GrabberGenericRound)
        self.addGrabber(0.5, 1, DIR_Y1, GrabberGenericRectangle)
        self.addGrabber(1, 0, DIR_X1 | DIR_Y0, GrabberGenericRound)
        self.addGrabber(0, 0.5, DIR_X0, GrabberGenericRectangle)

        self.c4 = self.figure.canvas.mpl_connect("key_press_event", self.keyPressEvent)

        self.targets: list[TargetWrapper] = []
        self.targets_rects: list[QtWidgets.QGraphicsRectItem] = []

        self.hide_grabber()

    def add_target(self, target: Artist):
        """add an artist to the selection"""
        target_wrapped = TargetWrapper(target)

        new_points = np.array(target_wrapped.get_positions())
        if len(new_points) == 0:
            return

        self.targets.append(target_wrapped)

        if new_points.shape[0] == 3:
            x0, y0, x1, y1 = (
                np.min(new_points[1:, 0]),
                np.min(new_points[1:, 1]),
                np.max(new_points[1:, 0]),
                np.max(new_points[1:, 1]),
            )
        else:
            x0, y0, x1, y1 = (
                np.min(new_points[:, 0]),
                np.min(new_points[:, 1]),
                np.max(new_points[:, 0]),
                np.max(new_points[:, 1]),
            )
        if 0:
            rect1 = Rectangle(
                (x0, y0),
                x1 - x0,
                y1 - y0,
                picker=False,
                figure=self.figure,
                linestyle="-",
                edgecolor="w",
                facecolor="#FFFFFF00",
                zorder=900,
                label="_rect for %s" % str(target),
            )
            rect2 = Rectangle(
                (x0, y0),
                x1 - x0,
                y1 - y0,
                picker=False,
                figure=self.figure,
                linestyle="--",
                edgecolor="k",
                facecolor="#FFFFFF00",
                zorder=900,
                label="_rect2 for %s" % str(target),
            )
            self.figure.patches.append(rect1)
            self.figure.patches.append(rect2)
            self.targets_rects.append(rect1)
            self.targets_rects.append(rect2)
        else:
            pen1 = QtGui.QPen(QtGui.QColor("white"), 2)
            pen2 = QtGui.QPen(QtGui.QColor("black"), 2)
            pen2.setStyle(QtCore.Qt.PenStyle.DashLine)
            # pen3 = QtGui.QPen(QtGui.QColor("black"), 2)
            # brush1 = QtGui.QBrush(QtGui.QColor("red"))

            w0, h0 = x1 - x0, y1 - y0
            rect1 = QtWidgets.QGraphicsRectItem(
                x0, y0, w0, h0, self.graphics_scene_myparent
            )
            rect1.setPen(pen1)
            rect2 = QtWidgets.QGraphicsRectItem(
                x0, y0, w0, h0, self.graphics_scene_myparent
            )
            rect2.setPen(pen2)

            self.targets_rects.append(rect1)
            self.targets_rects.append(rect2)

        self.update_extent()

    def update_extent(self):
        """updates the extend of the selection to all the selected elements"""
        points = None
        for target in self.targets:
            new_points = np.array(target.get_positions())

            if points is None:
                points = new_points
            else:
                points = np.concatenate((points, new_points))

        if points is None:
            return

        for grabber in self.grabbers:
            grabber.targets = self.targets

        self.positions[0] = np.min(points[:, 0])
        self.positions[1] = np.min(points[:, 1])
        self.positions[2] = np.max(points[:, 0])
        self.positions[3] = np.max(points[:, 1])

        if self.positions[2] - self.positions[0] < 0.01:
            self.positions[0], self.positions[2] = (
                self.positions[0] - 0.01,
                self.positions[0] + 0.01,
            )
        if self.positions[3] - self.positions[1] < 0.01:
            self.positions[1], self.positions[3] = (
                self.positions[1] - 0.01,
                self.positions[1] + 0.01,
            )

        if self.do_target_scale():
            self.update_grabber()
        else:
            self.hide_grabber()

    def align_points(self, mode: str):
        """a function to apply the alignment options, e.g. align all selected elements at the top or with equal spacing."""
        if len(self.targets) == 0:
            return

        if mode == "group":
            from pylustrator.helper_functions import axes_to_grid

            # return axes_to_grid([target.target for target in self.targets], track_changes=True)
            with UndoRedo(
                [
                    target.target
                    for target in self.targets
                    if isinstance(target.target, Axes)
                ],
                "Grid Align",
            ):
                axes_to_grid(
                    [
                        target.target
                        for target in self.targets
                        if isinstance(target.target, Axes)
                    ],
                    track_changes=False,
                )

        def align(y: int, func: Callable):
            self.start_move()
            centers = []
            for target in self.targets:
                new_points = np.array(target.get_positions())
                centers.append(func(new_points[:, y]))
            new_center = func(self.positions[y::2])
            for index, target in enumerate(self.targets):
                new_points = np.array(target.get_positions())
                new_points[:, y] += new_center - centers[index]
                target.set_positions(new_points)
            self.update_extent()
            self.has_moved = True
            self.end_move()

            self.figure.canvas.draw()
            self.update_selection_rectangles()

        def distribute(y: int):
            self.start_move()
            sizes = []
            positions = []
            for target in self.targets:
                new_points = np.array(target.get_positions())
                sizes.append(np.diff(new_points[:, y])[0])
                positions.append(np.min(new_points[:, y]))
            order = np.argsort(positions)
            spaces = np.diff(self.positions[y::2])[0] - np.sum(sizes)
            spaces /= max([(len(self.targets) - 1), 1])
            pos = np.min(self.positions[y::2])
            for index in order:
                target = self.targets[index]
                new_points = np.array(target.get_positions())
                new_points[:, y] += pos - np.min(new_points[:, y])
                target.set_positions(new_points)
                pos += sizes[index] + spaces
            self.has_moved = True
            self.end_move()

            self.figure.canvas.draw()
            self.update_selection_rectangles()

        if mode == "center_x":
            align(0, np.mean)

        if mode == "left_x":
            align(0, np.min)

        if mode == "right_x":
            align(0, np.max)

        if mode == "center_y":
            align(1, np.mean)

        if mode == "bottom_y":
            align(1, np.min)

        if mode == "top_y":
            align(1, np.max)

        if mode == "distribute_x":
            distribute(0)

        if mode == "distribute_y":
            distribute(1)

        self.figure.signals.figure_selection_moved.emit()

    def update_selection_rectangles(self, use_previous_offset=False):
        """update the selection visualisation"""
        if len(self.targets) == 0:
            return
        if 0:
            for index, target in enumerate(self.targets):
                new_points = np.array(target.get_positions())
                for i in range(2):
                    rect = self.targets_rects[index * 2 + i]
                    rect.set_xy(new_points[0])
                    rect.set_width(new_points[1][0] - new_points[0][0])
                    rect.set_height(new_points[1][1] - new_points[0][1])
        else:
            for index, target in enumerate(self.targets):
                new_points = np.array(
                    target.get_positions(use_previous_offset, update_offset=True)
                )
                if new_points.shape[0] == 3:
                    x0, y0, x1, y1 = (
                        np.min(new_points[1:, 0]),
                        np.min(new_points[1:, 1]),
                        np.max(new_points[1:, 0]),
                        np.max(new_points[1:, 1]),
                    )
                else:
                    x0, y0, x1, y1 = (
                        np.min(new_points[:, 0]),
                        np.min(new_points[:, 1]),
                        np.max(new_points[:, 0]),
                        np.max(new_points[:, 1]),
                    )
                w0, h0 = x1 - x0, y1 - y0
                for i in range(2):
                    rect = self.targets_rects[index * 2 + i]
                    rect.setRect(x0, y0, w0, h0)

    def remove_target(self, target: Artist):
        """remove an artist from the current selection"""
        targets_non_wrapped = [t.target for t in self.targets]
        if target not in targets_non_wrapped:
            return
        index = targets_non_wrapped.index(target)
        self.targets.pop(index)
        rect1 = self.targets_rects.pop(index * 2)
        rect2 = self.targets_rects.pop(index * 2)
        rect1_scene = rect1.scene()
        if rect1_scene is not None:
            rect1_scene.removeItem(rect1)
        rect2_scene = rect1.scene()
        if rect2_scene is not None:
            rect2_scene.removeItem(rect2)
        # self.figure.patches.remove(rect1)
        # self.figure.patches.remove(rect2)
        if len(self.targets) == 0:
            self.clear_targets()
        else:
            self.update_extent()

    def update_grabber(self):
        """update the position of the grabber elements"""
        if self.do_target_scale():
            for grabber in self.grabbers:
                grabber.updatePos()
        else:
            self.hide_grabber()

    def hide_grabber(self):
        """hide the grabber elements"""
        for grabber in self.grabbers:
            grabber.set_xy((-100, -100))

    def clear_targets(self):
        """remove all elements from the selection"""
        for rect in self.targets_rects:
            scene = self.graphics_scene.scene()
            if scene is not None:
                scene.removeItem(rect)
            # self.figure.patches.remove(rect)
        self.targets_rects = []
        self.targets = []

        self.hide_grabber()

    def do_target_scale(self) -> bool:
        """if any of the elements in the selection allows scaling"""
        return any([target.do_scale for target in self.targets])

    def do_change_aspect_ratio(self) -> bool:
        """if any of the element sin the selection wants to perserve its aspect ratio"""
        return any([target.fixed_aspect for target in self.targets])

    def width(self) -> float:
        """the width of the current selection"""
        return (self.p2 - self.p1)[0]

    def height(self) -> float:
        """the height of the current selection"""
        return (self.p2 - self.p1)[1]

    def size(self) -> Tuple[float, float]:
        """the size of the current selection (width and height)"""
        return self.p2 - self.p1

    def get_trans_matrix(self):
        """the transformation matrix for the current displacement and scaling of the selection"""
        x, y = self.p1
        w, h = self.size()
        return np.array([[w, 0, x], [0, h, y], [0, 0, 1]], dtype=float)

    def get_inv_trans_matrix(self):
        """the inverse transformation for the current displacement and scaling of the selection"""
        x, y = self.p1
        w, h = self.size()
        return np.array(
            [[1.0 / w, 0, -x / w], [0, 1.0 / h, -y / h], [0, 0, 1]], dtype=float
        )

    def transform(self, pos: Sequence) -> np.ndarray:
        """apply the current transformation to a point"""
        return np.dot(self.get_trans_matrix(), [pos[0], pos[1], 1.0])

    def inv_transform(self, pos: Sequence) -> np.ndarray:
        """apply the inverse current transformation to a point"""
        return np.dot(self.get_inv_trans_matrix(), [pos[0], pos[1], 1.0])

    def get_pos(self, pos: Sequence) -> np.ndarray:
        """transform a point"""
        return self.transform(pos)

    def get_save_point(self) -> Callable:
        """gather the current positions in a restore point for the undo function"""
        targets = [target.target for target in self.targets]
        positions = [target.get_positions() for target in self.targets]

        def undo():
            self.clear_targets()
            for target, pos in zip(targets, positions):
                target = TargetWrapper(target)
                target.set_positions(pos)
                self.add_target(target.target)

        return undo

    def start_move(self):
        """start to move a grabber"""
        self.start_p1 = self.p1.copy()
        self.start_p2 = self.p2.copy()
        self.hide_grabber()
        self.has_moved = False

        self.store_start = self.get_save_point()

    def end_move(self):
        """a grabber move stopped"""
        self.update_grabber()

        self.store_end = self.get_save_point()
        if self.has_moved is True:
            self.figure.signals.figure_selection_moved.emit()
            self.figure.change_tracker.addEdit(
                [self.store_start, self.store_end, "Move"]
            )

    def addOffset(self, pos: Sequence, dir: int, keep_aspect_ratio: bool = True):
        """move the whole selection (e.g. for the use of the arrow keys)"""
        pos = list(pos)
        self.old_inv_transform = self.get_inv_trans_matrix()

        if (keep_aspect_ratio or self.do_change_aspect_ratio()) and not (
            dir & DIR_X0 and dir & DIR_X1 and dir & DIR_Y0 and dir & DIR_Y1
        ):
            if (dir & DIR_X0 and dir & DIR_Y0) or (dir & DIR_X1 and dir & DIR_Y1):
                dx = pos[1] * self.width() / self.height()
                dy = pos[0] * self.height() / self.width()
                if abs(dx) < abs(dy):
                    pos[0] = dx
                else:
                    pos[1] = dy
            elif (dir & DIR_X0 and dir & DIR_Y1) or (dir & DIR_X1 and dir & DIR_Y0):
                dx = -pos[1] * self.width() / self.height()
                dy = -pos[0] * self.height() / self.width()
                if abs(dx) < abs(dy):
                    pos[0] = dx
                else:
                    pos[1] = dy
            elif dir & DIR_X0 or dir & DIR_X1:
                dy = pos[0] * self.height() / self.width()
                if dir & DIR_X0:
                    self.p1[1] = self.start_p1[1] + dy / 2
                    self.p2[1] = self.start_p2[1] - dy / 2
                else:
                    self.p1[1] = self.start_p1[1] - dy / 2
                    self.p2[1] = self.start_p2[1] + dy / 2
            elif dir & DIR_Y0 or dir & DIR_Y1:
                dx = pos[1] * self.width() / self.height()
                if dir & DIR_Y0:
                    self.p1[0] = self.start_p1[0] + dx / 2
                    self.p2[0] = self.start_p2[0] - dx / 2
                else:
                    self.p1[0] = self.start_p1[0] - dx / 2
                    self.p2[0] = self.start_p2[0] + dx / 2

        if dir & DIR_X0:
            self.p1[0] = self.start_p1[0] + pos[0]
        if dir & DIR_X1:
            self.p2[0] = self.start_p2[0] + pos[0]
        if dir & DIR_Y0:
            self.p1[1] = self.start_p1[1] + pos[1]
        if dir & DIR_Y1:
            self.p2[1] = self.start_p2[1] + pos[1]

        transform = np.dot(self.get_trans_matrix(), self.old_inv_transform)
        for target in self.targets:
            self.transform_target(transform, target)

        self.update_selection_rectangles(True)
        # for rect in self.targets_rects:
        #    self.transform_target(transform, TargetWrapper(rect))

    def move(
        self,
        pos: Sequence[float],
        dir: int,
        snaps: List[SnapBase],
        keep_aspect_ratio: bool = False,
        ignore_snaps: bool = False,
    ):
        """called from a grabber to move the selection."""
        self.addOffset(pos, dir, keep_aspect_ratio)
        self.has_moved = True

        if not ignore_snaps:
            offx, offy = checkSnaps(snaps)
            self.addOffset((pos[0] - offx, pos[1] - offy), dir, keep_aspect_ratio)

            checkSnaps(self.snaps)

        checkSnapsActive(snaps)

    def apply_transform(self, transform: np.ndarray, point: Sequence[float]):
        """apply the given transformation to a point"""
        point = np.array(point)
        point = np.hstack((point, np.ones((point.shape[0], 1)))).T
        return np.dot(transform, point)[:2].T

    def transform_target(self, transform: np.ndarray, target: TargetWrapper):
        """transform the position of an artist."""
        points = target.get_positions()
        points = self.apply_transform(transform, points)
        target.set_positions(points)

    def keyPressEvent(self, event: KeyEvent):
        """when a key is pressed. Arrow keys move the selection, Pageup/down movein z"""
        # if not self.selected:
        #    return
        # move last axis in z order
        if event.key == "pagedown":
            for target in self.targets:
                target.target.set_zorder(target.target.get_zorder() - 1)
                self.figure.change_tracker.addChange(
                    target.target, ".set_zorder(%d)" % target.target.get_zorder()
                )
            self.figure.canvas.draw()
        if event.key == "pageup":
            for target in self.targets:
                target.target.set_zorder(target.target.get_zorder() + 1)
                self.figure.change_tracker.addChange(
                    target.target, ".set_zorder(%d)" % target.target.get_zorder()
                )
            self.figure.canvas.draw()
        if event.key == "left":
            self.start_move()
            self.addOffset((-1, 0), self.dir)
            self.has_moved = True
            self.end_move()
            self.figure.canvas.schedule_draw()
        if event.key == "right":
            self.start_move()
            self.addOffset((+1, 0), self.dir)
            self.has_moved = True
            self.end_move()
            self.figure.canvas.schedule_draw()
        if event.key == "down":
            self.start_move()
            self.addOffset((0, -1), self.dir)
            self.has_moved = True
            self.end_move()
            self.figure.canvas.schedule_draw()
        if event.key == "up":
            self.start_move()
            self.addOffset((0, +1), self.dir)
            self.has_moved = True
            self.end_move()
            self.figure.canvas.schedule_draw()
        if event.key == "delete":
            for target in self.targets[::-1]:
                self.figure.change_tracker.removeElement(target.target)
            self.figure.canvas.draw()


class DragManager:
    """a class to manage the selection and the moving of artists in a figure"""

    selected_element = None
    grab_element = None

    def __init__(self, figure: Figure, no_save):
        self.figure = figure
        self.figure.figure_dragger = self

        manager = getattr(self.figure.canvas, "manager", None)
        cid = getattr(manager, "key_press_handler_id", None)
        if isinstance(cid, int):
            self.figure.canvas.mpl_disconnect(cid)

        self.activate()

        self.make_figure_draggable(self.figure)
        self.make_axes_draggable(self.figure.axes)
        graphics_scene = cast(
            "GraphicsRectItemWithView", getattr(figure, "_pyl_scene", None)
        )
        self.selection = GrabbableRectangleSelection(figure, graphics_scene)
        self.figure.selection = self.selection
        self.change_tracker = ChangeTracker(figure, no_save)
        self.figure.change_tracker = self.change_tracker

    def activate(self):
        """activate the interaction callbacks from the figure"""
        self.c3 = self.figure.canvas.mpl_connect(
            "button_release_event", self.button_release_event0
        )
        self.c2 = self.figure.canvas.mpl_connect(
            "button_press_event", self.button_press_event0
        )
        self.c4 = self.figure.canvas.mpl_connect(
            "key_press_event", self.key_press_event
        )

    def deactivate(self):
        """deactivate the interaction callbacks from the figure"""
        self.figure.canvas.mpl_disconnect(self.c3)
        self.figure.canvas.mpl_disconnect(self.c2)
        self.figure.canvas.mpl_disconnect(self.c4)

        self.selection.clear_targets()
        self.selected_element = None
        self.on_select(None, None)
        self.figure.canvas.draw()

    def make_draggable(self, target: Artist):
        """make an artist draggable"""
        target.set_picker(True)
        if isinstance(target, Text):
            target.set_bbox(dict(facecolor="none", edgecolor="none"))

    def make_axes_draggable(self, axes: list[Axes]) -> None:
        for index, ax in enumerate(axes):
            ax.set_picker(True)
            leg = ax.get_legend()
            if leg:
                self.make_draggable(leg)
            for text in ax.texts:
                self.make_draggable(text)
            for attribute_name in ["title", "_left_title", "_right_title"]:
                text = getattr(ax, attribute_name, None)
                if text is not None:
                    self.make_draggable(text)
            for patch in ax.patches:
                self.make_draggable(patch)
            self.make_draggable(ax.xaxis.get_label())
            self.make_draggable(ax.yaxis.get_label())
            self.make_draggable(ax)
            self.make_axes_draggable([a for a in ax.child_axes if isinstance(a, Axes)])

    def make_figure_draggable(self, fig: Figure | SubFigure) -> None:
        for text in fig.texts:
            self.make_draggable(text)
        for patch in fig.patches:
            self.make_draggable(patch)
        for leg in fig.legends:
            self.make_draggable(leg)
        for subfig in fig.subfigs:
            self.make_figure_draggable(subfig)

    def get_picked_element(
        self,
        event: MouseEvent,
        element: Artist | Figure | None = None,
        picked_element: Artist | None = None,
        last_selected: Artist | None = None,
    ):
        """get the picked element that an event refers to.
        To implement selection of elements at the back with multiple clicks.
        """
        if not isinstance(element, (Artist, Figure)):
            element = self.figure
        if not isinstance(element, (Artist, Figure)):
            raise ValueError("element must be an Artist or Figure")

        finished = False
        # iterate over all children
        for child in sorted(
            cast(Artist, element).get_children(), key=lambda x: x.get_zorder()
        ):
            # check if the element is contained in the event and has an active dragger
            # if child.contains(event)[0] and ((getattr(child, "_draggable", None) and getattr(child, "_draggable",
            #                                                                               None).connected) or isinstance(child, GrabberGeneric) or isinstance(child, GrabbableRectangleSelection)):
            child_label = child.get_label()
            is_underscored = (
                child_label is not None
                and isinstance(child_label, str)
                and child_label.startswith("_")
            )
            if (
                child.get_visible()
                and child.contains(event)[0]
                and (child.pickable() or isinstance(child, GrabberGeneric))
                and not is_underscored
            ):
                # if the element is the last selected, finish the search
                if child == last_selected:
                    return picked_element, True
                # use this element as the current best matching element
                picked_element = child
            # iterate over the children's children
            picked_element, finished = self.get_picked_element(
                event, child, picked_element, last_selected=last_selected
            )
            # if the subcall wants to finish, just break the loop
            if finished:
                break
        return picked_element, finished

    def button_release_event0(self, event: Event):
        """when the mouse button is released"""
        event = cast(MouseEvent, event)
        # release the grabber
        if self.grab_element:
            self.grab_element.button_release_event(event)
            self.grab_element = None
        # or notify the selected element
        elif len(self.selection.targets):
            self.selection.button_release_event(event)

    def button_press_event0(self, event: Event):
        """when the mouse button is pressed"""
        event = cast(MouseEvent, event)
        if event.button == 1:
            last = self.selection.targets[-1] if len(self.selection.targets) else None
            contained = np.any(
                [t.target.contains(event)[0] for t in self.selection.targets]
            )

            # recursively iterate over all elements
            picked_element, _ = self.get_picked_element(
                event,
                last_selected=(
                    last.target if (event.dblclick and last is not None) else None
                ),
            )

            # if the element is a grabber, store it
            if isinstance(picked_element, GrabberGeneric):
                self.grab_element = picked_element
            # if not, we want to keep our selected element, if the click was in the area of the selected element
            elif len(self.selection.targets) == 0 or not contained or event.dblclick:
                self.select_element(picked_element, event)
                contained = True

            # if we have a grabber, notify it
            if self.grab_element:
                self.grab_element.button_press_event(event)
            # if not, notify the selected element
            elif contained:
                self.selection.button_press_event(event)

    def select_element(self, element: Artist, event: MouseEvent | None = None):
        """select an artist in a figure"""
        # do nothing if it is already selected
        if element == self.selected_element:
            return
        # if there was was previously selected element, deselect it
        if self.selected_element is not None and event is not None:
            self.on_deselect(event)

        # if there is a new element, select it
        self.on_select(element, event)
        self.selected_element = element

    def on_deselect(self, event: MouseEvent):
        """deselect currently selected artists"""
        modifier = (
            "shift" in event.key.split("+")
            if event is not None and event.key is not None
            else False
        )
        # only if the modifier key is not used
        if not modifier:
            self.selection.clear_targets()

    def on_select(self, element: Artist | None, event: MouseEvent | None):
        """when an artist is selected"""
        if element is not None:
            self.selection.add_target(element)

    def undo(self):
        print("back edit")
        self.figure.change_tracker.backEdit()
        self.selection.clear_targets()
        self.selected_element = None
        self.on_select(None, None)
        self.figure.canvas.draw()

    def redo(self):
        print("forward edit")
        self.figure.change_tracker.forwardEdit()
        self.selection.clear_targets()
        self.selected_element = None
        self.on_select(None, None)
        self.figure.canvas.draw()

    def key_press_event(self, event: Event):
        """when a key is pressed"""
        event = cast(KeyEvent, event)
        # space: print code to restore current configuration
        if event.key == "ctrl+s":
            self.figure.change_tracker.save()
        if event.key == "ctrl+z":
            self.undo()
        if event.key == "ctrl+y":
            self.redo()
        if event.key == "escape":
            self.selection.clear_targets()
            self.selected_element = None
            self.on_select(None, None)
            self.figure.canvas.draw()


class GrabberGeneric(GrabFunctions):
    """a generic grabber object to move a selection"""

    _no_save = True

    def __init__(
        self,
        parent: "GrabbableRectangleSelection",
        x: float,
        y: float,
        dir: int,
        scene: Any | None = None,
    ):
        self._animated = True
        GrabFunctions.__init__(self, parent, dir)
        self.pos = (x, y)
        self.updatePos()

    def get_xy(self):
        return self.center

    def set_xy(self, xy: tuple[float, float]):
        self.center = xy

    def getPos(self):
        x, y = self.get_xy()
        t = getattr(self, "transform", None)
        if t is None:
            return x, y
        return t.transform((x, y))

    def updatePos(self):
        self.set_xy(self.parent.get_pos(self.pos))


class GrabberGenericRound(GrabberGeneric):
    """a rectangle with a round appearance"""

    d = 10
    shape = "round"

    def __init__(
        self,
        parent: GrabbableRectangleSelection,
        x: float,
        y: float,
        dir: int,
        scene: "GraphicsRectItemWithView",
    ):
        pen3 = QtGui.QPen(QtGui.QColor("black"), 2)
        brush1 = QtGui.QBrush(QtGui.QColor("red"))

        self.ellipse = MyEllipse(x, y, 10, 10, scene)
        self.ellipse.view = scene.view
        self.ellipse.grabber = self
        self.ellipse.setPen(pen3)
        self.ellipse.setBrush(brush1)
        self.center = (x, y)

        GrabberGeneric.__init__(self, parent, x, y, dir)

    def set_xy(self, xy: tuple[float, float]):
        self.xy = xy
        self.ellipse.setRect(xy[0] - 5, xy[1] - 5, 10, 10)
        self.ellipse.setRect(xy[0] - 5, xy[1] - 5, 10, 10)


class GrabberGenericRectangle(GrabberGeneric):
    """a rectangle with a square appearance"""

    d = 10
    shape = "rect"

    def __init__(
        self,
        parent: GrabbableRectangleSelection,
        x: float,
        y: float,
        dir: int,
        scene: "GraphicsRectItemWithView",
    ):
        # somehow the original "self" rectangle does not show up in the current matplotlib version, therefore this doubling
        # self.rect = Rectangle((0, 0), self.d, self.d, figure=parent.figure, edgecolor="k", facecolor="r", zorder=1000, label="grabber")
        # self.rect._no_save = True
        # parent.figure.patches.append(self.rect)

        # Rectangle.__init__(self, (0, 0), self.d, self.d, picker=True, figure=parent.figure, edgecolor="k", facecolor="r", zorder=1000, label="grabber")

        # self.figure.patches.append(self)

        pen3 = QtGui.QPen(QtGui.QColor("black"), 2)
        brush1 = QtGui.QBrush(QtGui.QColor("red"))

        self.ellipse = MyRect(x - 5, y - 5, 10, 10, scene)
        self.ellipse.view = scene.view
        self.ellipse.grabber = self
        self.ellipse.setPen(pen3)
        self.ellipse.setBrush(brush1)

        self.xy = (x, y)
        # self.updatePos()

        GrabberGeneric.__init__(self, parent, x, y, dir)

    def get_xy(self):
        return self.xy
        xy = Rectangle.get_xy(self)
        return xy[0] + self.d / 2, xy[1] + self.d / 2

    def set_xy(self, xy: Tuple[float, float]):
        self.xy = xy

        self.ellipse.setRect(xy[0] - 5, xy[1] - 5, 10, 10)
        return
        Rectangle.set_xy(self, (xy[0] - self.d / 2, xy[1] - self.d / 2))
        self.rect.set_xy((xy[0] - self.d / 2, xy[1] - self.d / 2))


class MyItem:
    w = 10
    view: Any
    grabber: Any
    scene: Callable[[], Any]

    def mousePressEvent(self, e):
        cast(Any, super()).mousePressEvent(e)
        cast(Any, self).view.grabber_found = True
        p = e.scenePos()
        self.scene().grabber_pressed = self
        cast(Any, self).grabber.button_press_event(
            MyEvent(p.x(), cast(Any, self).view.h - p.y())
        )

    def mouseReleaseEvent(self, e):
        cast(Any, super()).mouseReleaseEvent(e)
        self.scene().grabber_pressed = None
        cast(Any, self).view.grabber_found = True
        p = e.scenePos()
        cast(Any, self).grabber.button_release_event(
            MyEvent(p.x(), cast(Any, self).view.h - p.y())
        )


class MyRect(MyItem, QtWidgets.QGraphicsRectItem):
    view = None
    grabber = None
    pass


class MyEllipse(MyItem, QtWidgets.QGraphicsEllipseItem):
    view = None
    grabber = None
    pass


class MyEvent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
