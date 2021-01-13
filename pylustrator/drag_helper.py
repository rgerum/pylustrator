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

from __future__ import division, print_function
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.figure import Figure
from matplotlib.text import Text
from matplotlib.patches import Rectangle, Ellipse
from matplotlib.backend_bases import MouseEvent, KeyEvent
from typing import Sequence

from .snap import TargetWrapper, getSnaps, checkSnaps, checkSnapsActive, SnapBase
from .change_tracker import ChangeTracker

DIR_X0 = 1
DIR_Y0 = 2
DIR_X1 = 4
DIR_Y1 = 8


class GrabFunctions(object):
    """ basic functionality used by all grabbers """
    figure = None
    target = None
    dir = None
    snaps = None

    got_artist = False

    def __init__(self, parent, dir: int, no_height=False):
        self.figure = parent.figure
        self.parent = parent
        self.dir = dir
        self.snaps = []
        self.no_height = no_height

    def on_motion(self, evt: MouseEvent):
        """ callback when the object is moved """
        if self.got_artist:
            self.movedEvent(evt)
            self.moved = True

    def button_press_event(self, evt: MouseEvent):
        """ when the mouse is pressed """
        self.got_artist = True
        self.moved = False

        self._c1 = self.figure.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.clickedEvent(evt)

    def button_release_event(self, event: MouseEvent):
        """ when the mouse is released """
        if self.got_artist:
            self.got_artist = False
            self.figure.canvas.mpl_disconnect(self._c1)
            self.releasedEvent(event)

    def clickedEvent(self, event: MouseEvent):
        """ when the mouse is clicked """
        self.parent.start_move()
        self.mouse_xy = (event.x, event.y)

        for s in self.snaps:
            s.remove()
        self.snaps = []

        self.snaps = getSnaps(self.targets, self.dir, no_height=self.no_height)

    def releasedEvent(self, event: MouseEvent):
        """ when the mouse is released """
        for snap in self.snaps:
            snap.remove()
        self.snaps = []

        self.parent.end_move()

    def movedEvent(self, event: MouseEvent):
        """ when the mouse is moved """
        if len(self.targets) == 0:
            return

        dx = event.x - self.mouse_xy[0]
        dy = event.y - self.mouse_xy[1]

        keep_aspect = ("control" in event.key.split("+") if event.key is not None else False)
        ignore_snaps = ("shift" in event.key.split("+") if event.key is not None else False)

        self.parent.move([dx, dy], self.dir, self.snaps, keep_aspect_ratio=keep_aspect, ignore_snaps=ignore_snaps)


class GrabbableRectangleSelection(GrabFunctions):
    grabbers = None

    def addGrabber(self, x: float, y: float, dir: int, GrabberClass: object):
        # add a grabber object at the given coordinates
        self.grabbers.append(GrabberClass(self, x, y, dir))

    def __init__(self, figure: Figure):
        self.grabbers = []
        pos = [0, 0, 0, 0]
        self.positions = np.array(pos, dtype=float)
        self.p1 = self.positions[:2]
        self.p2 = self.positions[2:]
        self.figure = figure

        GrabFunctions.__init__(self, self, DIR_X0 | DIR_X1 | DIR_Y0 | DIR_Y1, no_height=True)

        self.addGrabber(0,   0, DIR_X0 | DIR_Y0, GrabberGenericRound)
        self.addGrabber(0.5, 0, DIR_Y0, GrabberGenericRectangle)
        self.addGrabber(1,   1, DIR_X1 | DIR_Y1, GrabberGenericRound)
        self.addGrabber(1, 0.5, DIR_X1, GrabberGenericRectangle)
        self.addGrabber(0,   1, DIR_X0 | DIR_Y1, GrabberGenericRound)
        self.addGrabber(0.5, 1, DIR_Y1, GrabberGenericRectangle)
        self.addGrabber(1,   0, DIR_X1 | DIR_Y0, GrabberGenericRound)
        self.addGrabber(0, 0.5, DIR_X0, GrabberGenericRectangle)

        self.c4 = self.figure.canvas.mpl_connect('key_press_event', self.keyPressEvent)

        self.targets = []
        self.targets_rects = []

        self.hide_grabber()

    def add_target(self, target: Artist):
        """ add an artist to the selection """
        target = TargetWrapper(target)

        new_points = np.array(target.get_positions())
        if len(new_points) == 0:
            return

        self.targets.append(target)

        x0, y0, x1, y1 = np.min(new_points[:, 0]), np.min(new_points[:, 1]), np.max(new_points[:, 0]), np.max(
            new_points[:, 1])
        rect1 = Rectangle((x0, y0), x1 - x0, y1 - y0, picker=False, figure=self.figure, linestyle="-", edgecolor="w",
                          facecolor="#FFFFFF00", zorder=900, label="_rect for %s" % str(target))
        rect2 = Rectangle((x0, y0), x1 - x0, y1 - y0, picker=False, figure=self.figure, linestyle="--", edgecolor="k",
                          facecolor="#FFFFFF00", zorder=900, label="_rect2 for %s" % str(target))
        self.figure.patches.append(rect1)
        self.figure.patches.append(rect2)
        self.targets_rects.append(rect1)
        self.targets_rects.append(rect2)

        self.update_extent()

    def update_extent(self):
        """ updates the extend of the selection to all the selected elements """
        points = None
        for target in self.targets:
            new_points = np.array(target.get_positions())

            if points is None:
                points = new_points
            else:
                points = np.concatenate((points, new_points))

        for grabber in self.grabbers:
            grabber.targets = self.targets

        self.positions[0] = np.min(points[:, 0])
        self.positions[1] = np.min(points[:, 1])
        self.positions[2] = np.max(points[:, 0])
        self.positions[3] = np.max(points[:, 1])

        if self.positions[2]-self.positions[0] < 0.01:
            self.positions[0], self.positions[2] = self.positions[0] - 0.01, self.positions[0] + 0.01
        if self.positions[3]-self.positions[1] < 0.01:
            self.positions[1], self.positions[3] = self.positions[1] - 0.01, self.positions[1] + 0.01

        if self.do_target_scale():
            self.update_grabber()
        else:
            self.hide_grabber()

    def align_points(self, mode: str):
        """ a function to apply the alignment options, e.g. align all selected elements at the top or with equal spacing. """
        if len(self.targets) == 0:
            return

        if mode == "group":
            from pylustrator.helper_functions import axes_to_grid
            return axes_to_grid([target.target for target in self.targets], track_changes=True)

        def align(y: int, func: callable):
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

        def distribute(y: int):
            sizes = []
            positions = []
            for target in self.targets:
                new_points = np.array(target.get_positions())
                sizes.append(np.diff(new_points[:, y])[0])
                positions.append(np.min(new_points[:, y]))
            order = np.argsort(positions)
            spaces = np.diff(self.positions[y::2])[0] - np.sum(sizes)
            spaces /= max([(len(self.targets)-1), 1])
            pos = np.min(self.positions[y::2])
            for index in order:
                target = self.targets[index]
                new_points = np.array(target.get_positions())
                new_points[:, y] += pos - np.min(new_points[:, y])
                target.set_positions(new_points)
                pos += sizes[index] + spaces

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

    def update_selection_rectangles(self):
        """ update the selection visualisation """
        if len(self.targets) == 0:
            return
        for index, target in enumerate(self.targets):
            new_points = np.array(target.get_positions())
            for i in range(2):
                rect = self.targets_rects[index*2+i]
                rect.set_xy(new_points[0])
                rect.set_width(new_points[1][0] - new_points[0][0])
                rect.set_height(new_points[1][1] - new_points[0][1])

        self.update_extent()

    def remove_target(self, target: Artist):
        """ remove an artist from the current selection """
        targets_non_wrapped = [t.target for t in self.targets]
        if target not in targets_non_wrapped:
            return
        index = targets_non_wrapped.index(target)
        self.targets.pop(index)
        rect1 = self.targets_rects.pop(index*2)
        rect2 = self.targets_rects.pop(index*2)
        self.figure.patches.remove(rect1)
        self.figure.patches.remove(rect2)
        if len(self.targets) == 0:
            self.clear_targets()
        else:
            self.update_extent()

    def update_grabber(self):
        """ update the position of the grabber elements """
        if self.do_target_scale():
            for grabber in self.grabbers:
                grabber.updatePos()
        else:
            self.hide_grabber()

    def hide_grabber(self):
        """ hide the grabber elements """
        for grabber in self.grabbers:
            grabber.set_xy((-100, -100))

    def clear_targets(self):
        """ remove all elements from the selection """
        for rect in self.targets_rects:
            self.figure.patches.remove(rect)
        self.targets_rects = []
        self.targets = []

        self.hide_grabber()

    def do_target_scale(self) -> bool:
        """ if any of the elements in the selection allows scaling """
        return np.any([target.do_scale for target in self.targets])

    def do_change_aspect_ratio(self) -> bool:
        """ if any of the element sin the selection wants to perserve its aspect ratio """
        return np.any([target.fixed_aspect for target in self.targets])

    def width(self) -> float:
        """ the width of the current selection """
        return (self.p2-self.p1)[0]

    def height(self) -> float:
        """ the height of the current selection """
        return (self.p2-self.p1)[1]

    def size(self) -> (float, float):
        """ the size of the current selection (width and height)"""
        return self.p2-self.p1

    def get_trans_matrix(self):
        """ the transformation matrix for the current displacement and scaling of the selection """
        x, y = self.p1
        w, h = self.size()
        return np.array([[w, 0, x], [0, h, y], [0, 0, 1]], dtype=float)

    def get_inv_trans_matrix(self):
        """ the inverse transformation for the current displacement and scaling of the selection """
        x, y = self.p1
        w, h = self.size()
        return np.array([[1./w, 0, -x/w], [0, 1./h, -y/h], [0, 0, 1]], dtype=float)

    def transform(self, pos: Sequence) -> np.ndarray:
        """ apply the current transformation to a point """
        return np.dot(self.get_trans_matrix(), [pos[0], pos[1], 1.0])

    def inv_transform(self, pos: Sequence) -> np.ndarray:
        """ apply the inverse current transformation to a point """
        return np.dot(self.get_inv_trans_matrix(), [pos[0], pos[1], 1.0])

    def get_pos(self, pos: Sequence) -> np.ndarray:
        """ transform a point """
        return self.transform(pos)

    def get_save_point(self) -> callable:
        """ gather the current positions in a restore point for the undo function """
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
        """ start to move a grabber """
        self.start_p1 = self.p1.copy()
        self.start_p2 = self.p2.copy()
        self.hide_grabber()

        self.store_start = self.get_save_point()

    def end_move(self):
        """ a grabber move stopped """
        self.update_grabber()
        self.figure.canvas.draw()

        self.store_end = self.get_save_point()
        self.figure.change_tracker.addEdit([self.store_start, self.store_end])

    def addOffset(self, pos: Sequence, dir: int, keep_aspect_ratio: bool = True):
        """ move the whole selection (e.g. for the use of the arrow keys) """
        pos = list(pos)
        self.old_inv_transform = self.get_inv_trans_matrix()

        if (keep_aspect_ratio or self.do_change_aspect_ratio()) and not (dir & DIR_X0 and dir & DIR_X1 and dir & DIR_Y0 and dir & DIR_Y1):
            if (dir & DIR_X0 and dir & DIR_Y0) or (dir & DIR_X1 and dir & DIR_Y1):
                dx = pos[1]*self.width()/self.height()
                dy = pos[0]*self.height()/self.width()
                if abs(dx) < abs(dy):
                    pos[0] = dx
                else:
                    pos[1] = dy
            elif (dir & DIR_X0 and dir & DIR_Y1) or (dir & DIR_X1 and dir & DIR_Y0):
                dx = -pos[1]*self.width()/self.height()
                dy = -pos[0]*self.height()/self.width()
                if abs(dx) < abs(dy):
                    pos[0] = dx
                else:
                    pos[1] = dy
            elif dir & DIR_X0 or dir & DIR_X1:
                dy = pos[0]*self.height()/self.width()
                if dir & DIR_X0:
                    self.p1[1] = self.start_p1[1] + dy/2
                    self.p2[1] = self.start_p2[1] - dy/2
                else:
                    self.p1[1] = self.start_p1[1] - dy / 2
                    self.p2[1] = self.start_p2[1] + dy / 2
            elif dir & DIR_Y0 or dir & DIR_Y1:
                dx = pos[1]*self.width()/self.height()
                if dir & DIR_Y0:
                    self.p1[0] = self.start_p1[0] + dx/2
                    self.p2[0] = self.start_p2[0] - dx/2
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

        for rect in self.targets_rects:
            self.transform_target(transform, TargetWrapper(rect))

    def move(self, pos: Sequence[float], dir: int, snaps: Sequence[SnapBase], keep_aspect_ratio: bool = False, ignore_snaps: bool = False):
        """ called from a grabber to move the selection. """
        self.addOffset(pos, dir, keep_aspect_ratio)

        if not ignore_snaps:
            offx, offy = checkSnaps(snaps)
            self.addOffset((pos[0]-offx, pos[1]-offy), dir, keep_aspect_ratio)

            offx, offy = checkSnaps(self.snaps)

        checkSnapsActive(snaps)

        self.figure.canvas.draw()

    def apply_transform(self, transform: np.ndarray, point: Sequence[float]):
        """ apply the given transformation to a point"""
        point = np.array(point)
        point = np.hstack((point, np.ones((point.shape[0], 1)))).T
        return np.dot(transform, point)[:2].T

    def transform_target(self, transform: np.ndarray, target: TargetWrapper):
        """ transform the position of an artist. """
        points = target.get_positions()
        points = self.apply_transform(transform, points)
        target.set_positions(points)

    def keyPressEvent(self, event: KeyEvent):
        """ when a key is pressed. Arrow keys move the selection, Pageup/down movein z """
        #if not self.selected:
        #    return
        # move last axis in z order
        if event.key == 'pagedown':
            for target in self.targets:
                target.target.set_zorder(target.target.get_zorder() - 1)
                self.figure.change_tracker.addChange(target.target, ".set_zorder(%d)" % target.target.get_zorder())
            self.figure.canvas.draw()
        if event.key == 'pageup':
            for target in self.targets:
                target.target.set_zorder(target.target.get_zorder() + 1)
                self.figure.change_tracker.addChange(target.target, ".set_zorder(%d)" % target.target.get_zorder())
            self.figure.canvas.draw()
        if event.key == 'left':
            self.start_move()
            self.addOffset((-1, 0), self.dir)
            self.end_move()
        if event.key == 'right':
            self.start_move()
            self.addOffset((+1, 0), self.dir)
            self.end_move()
        if event.key == 'down':
            self.start_move()
            self.addOffset((0, -1), self.dir)
            self.end_move()
        if event.key == 'up':
            self.start_move()
            self.addOffset((0, +1), self.dir)
            self.end_move()
        if event.key == "delete":
            for target in self.targets[::-1]:
                self.figure.change_tracker.removeElement(target.target)
            self.figure.canvas.draw()
        #print("event", event.key)


class DragManager:
    """ a class to manage the selection and the moving of artists in a figure """
    selected_element = None
    grab_element = None

    def __init__(self, figure: Figure):
        self.figure = figure
        self.figure.figure_dragger = self

        self.figure.canvas.mpl_disconnect(self.figure.canvas.manager.key_press_handler_id)

        self.activate()

        # make all the subplots pickable
        for index, axes in enumerate(self.figure.axes):
            axes.set_picker(True)
            leg = axes.get_legend()
            if leg:
                self.make_dragable(leg)
            for text in axes.texts:
                self.make_dragable(text)
            for attribute_name in ["title", "_left_title", "_right_title"]:
                text = getattr(axes, attribute_name, None)
                if text is not None:
                    self.make_dragable(text)
            for patch in axes.patches:
                self.make_dragable(patch)
            self.make_dragable(axes.xaxis.get_label())
            self.make_dragable(axes.yaxis.get_label())

            self.make_dragable(axes)
        for text in self.figure.texts:
            self.make_dragable(text)
        for patch in self.figure.patches:
            self.make_dragable(patch)

        self.selection = GrabbableRectangleSelection(figure)
        self.figure.selection = self.selection
        self.change_tracker = ChangeTracker(figure)
        self.figure.change_tracker = self.change_tracker

    def activate(self):
        """ activate the interaction callbacks from the figure """
        self.c3 = self.figure.canvas.mpl_connect('button_release_event', self.button_release_event0)
        self.c2 = self.figure.canvas.mpl_connect('button_press_event', self.button_press_event0)
        self.c4 = self.figure.canvas.mpl_connect('key_press_event', self.key_press_event)

    def deactivate(self):
        """ deactivate the interaction callbacks from the figure """
        self.figure.canvas.mpl_disconnect(self.c3)
        self.figure.canvas.mpl_disconnect(self.c2)
        self.figure.canvas.mpl_disconnect(self.c4)

        self.selection.clear_targets()
        self.selected_element = None
        self.on_select(None, None)
        self.figure.canvas.draw()

    def make_dragable(self, target: Artist):
        """ make an artist draggable """
        target.set_picker(True)
        if isinstance(target, Text):
            target.set_bbox(dict(facecolor="none", edgecolor="none"))

    def get_picked_element(self, event: MouseEvent, element: Artist = None, picked_element: Artist = None, last_selected: Artist = None):
        """ get the picked element that an event refers to.
        To implement selection of elements at the back with multiple clicks.
        """
        # start with the figure
        if element is None:
            element = self.figure
        finished = False
        # iterate over all children
        for child in sorted(element.get_children(), key=lambda x: x.get_zorder()):
            # check if the element is contained in the event and has an active dragger
            #if child.contains(event)[0] and ((getattr(child, "_draggable", None) and getattr(child, "_draggable",
            #                                                                               None).connected) or isinstance(child, GrabberGeneric) or isinstance(child, GrabbableRectangleSelection)):
            if child.get_visible() and child.contains(event)[0] and (child.pickable() or isinstance(child, GrabberGeneric)) and not (child.get_label() is not None and child.get_label().startswith("_")):
                # if the element is the last selected, finish the search
                if child == last_selected:
                    return picked_element, True
                # use this element as the current best matching element
                picked_element = child
            # iterate over the children's children
            picked_element, finished = self.get_picked_element(event, child, picked_element, last_selected=last_selected)
            # if the subcall wants to finish, just break the loop
            if finished:
                break
        return picked_element, finished

    def button_release_event0(self, event: MouseEvent):
        """ when the mouse button is released """
        # release the grabber
        if self.grab_element:
            self.grab_element.button_release_event(event)
            self.grab_element = None
        # or notify the selected element
        elif len(self.selection.targets):
            self.selection.button_release_event(event)

    def button_press_event0(self, event: MouseEvent):
        """ when the mouse button is pressed """
        if event.button == 1:
            last = self.selection.targets[-1] if len(self.selection.targets) else None
            contained = np.any([t.target.contains(event)[0] for t in self.selection.targets])

            # recursively iterate over all elements
            picked_element, _ = self.get_picked_element(event, last_selected=last if event.dblclick else None)

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

    def select_element(self, element: Artist, event: MouseEvent = None):
        """ select an artist in a figure """
        # do nothing if it is already selected
        if element == self.selected_element:
            return
        # if there was was previously selected element, deselect it
        if self.selected_element is not None:
            self.on_deselect(event)

        # if there is a new element, select it
        self.on_select(element, event)
        self.selected_element = element
        self.figure.canvas.draw()

    def on_deselect(self, event: MouseEvent):
        """ deselect currently selected artists"""
        modifier = "shift" in event.key.split("+") if event is not None and event.key is not None else False
        # only if the modifier key is not used
        if not modifier:
            self.selection.clear_targets()

    def on_select(self, element: Artist, event: MouseEvent):
        """ when an artist is selected """
        if element is not None:
            self.selection.add_target(element)

    def key_press_event(self, event: KeyEvent):
        """ when a key is pressed """
        # space: print code to restore current configuration
        if event.key == 'ctrl+s':
            self.figure.change_tracker.save()
        if event.key == "ctrl+z":
            self.figure.change_tracker.backEdit()
        if event.key == "ctrl+y":
            self.figure.change_tracker.forwardEdit()
        if event.key == "escape":
            self.selection.clear_targets()
            self.selected_element = None
            self.on_select(None, None)
            self.figure.canvas.draw()


class GrabberGeneric(GrabFunctions):
    """ a generic grabber object to move a selection """
    _no_save = True

    def __init__(self, parent: GrabbableRectangleSelection, x: float, y: float, dir: int):
        self._animated = True
        GrabFunctions.__init__(self, parent, dir)
        self.pos = (x, y)
        self.updatePos()

    def get_xy(self):
        return self.center

    def set_xy(self, xy: (float, float)):
        self.center = xy

    def getPos(self):
        x, y = self.get_xy()
        return self.transform.transform((x, y))

    def updatePos(self):
        self.set_xy(self.parent.get_pos(self.pos))

    def applyOffset(self, pos: (float, float), event: MouseEvent):
        self.set_xy((self.ox+pos[0], self.oy+pos[1]))


class GrabberGenericRound(Ellipse, GrabberGeneric):
    """ a rectangle with a round appearance """
    d = 10

    def __init__(self, parent: GrabbableRectangleSelection, x: float, y: float, dir: int):
        GrabberGeneric.__init__(self, parent, x, y, dir)
        Ellipse.__init__(self, (0, 0), self.d, self.d, picker=True, figure=parent.figure, edgecolor="k", facecolor="r", zorder=1000, label="grabber")
        self.figure.patches.append(self)
        self.updatePos()


class GrabberGenericRectangle(Rectangle, GrabberGeneric):
    """ a rectangle with a square appearance """
    d = 10

    def __init__(self, parent: GrabbableRectangleSelection, x: float, y: float, dir: int):
        # somehow the original "self" rectangle does not show up in the current matplotlib version, therefore this doubling
        self.rect = Rectangle((0, 0), self.d, self.d, figure=parent.figure, edgecolor="k", facecolor="r", zorder=1000, label="grabber")
        self.rect._no_save = True
        parent.figure.patches.append(self.rect)

        Rectangle.__init__(self, (0, 0), self.d, self.d, picker=True, figure=parent.figure, edgecolor="k", facecolor="r", zorder=1000, label="grabber")
        GrabberGeneric.__init__(self, parent, x, y, dir)
        self.figure.patches.append(self)
        self.updatePos()

    def get_xy(self):
        xy = Rectangle.get_xy(self)
        return xy[0] + self.d / 2, xy[1] + self.d / 2

    def set_xy(self, xy: (float, float)):
        Rectangle.set_xy(self, (xy[0] - self.d / 2, xy[1] - self.d / 2))
        self.rect.set_xy((xy[0] - self.d / 2, xy[1] - self.d / 2))
