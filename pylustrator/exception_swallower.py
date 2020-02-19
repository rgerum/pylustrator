#!/usr/bin/env python
# -*- coding: utf-8 -*-
# exception_swallower.py

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

from matplotlib.figure import Figure
from matplotlib.axes._base import _AxesBase
from matplotlib.axis import Axis


class Dummy:
    """ a dummy object that provides dummy attributes, dummy items and dummy returns """
    def __getattr__(self, item):
        return Dummy()

    def __call__(self, *args, **kwargs):
        return Dummy()

    def __getitem__(self, item):
        return Dummy()


class SaveList(list):
    """ a list that returns dummy objects when an invalid item is requested """
    def __init__(self, target):
        list.__init__(self, target)

    def __getitem__(self, item):
        try:
            return list.__getitem__(self, item)
        except IndexError:
            return Dummy()


class SaveDict(dict):
    """ a dictionary that returns dummy objects when an invalid item is requested """
    def __init__(self, target):
        dict.__init__(self, target)

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            return Dummy()


class SaveTuple(tuple):
    """ a tuple that returns dummy objects when an invalid item is requested """
    def __init__(self, target):
        tuple.__init__(self, target)

    def __getitem__(self, item):
        try:
            return tuple.__getitem__(self, item)
        except IndexError:
            return Dummy()


class SaveListDescriptor:
    """ a descriptor that wraps the target value with a SaveList, SaveDict or SaveTuple """
    def __init__(self, variable_name):
        self.variable_name = variable_name

    def __set__(self, instance, value):
        if isinstance(value, list):
            value = SaveList(value)
        if isinstance(value, dict):
            value = SaveDict(value)
        if isinstance(value, tuple):
            value = SaveTuple(value)
        setattr(instance, "_pylustrator_"+self.variable_name, value)

    def __get__(self, instance, owner):
        try:
            return getattr(instance, "_pylustrator_"+self.variable_name)
        except AttributeError:
            if self.variable_name in instance.__dict__:
                return instance.__dict__[self.variable_name]
            else:
                return SaveList([])


def get_axes(self):
    """ a function that returns the axes of a figure as a SaveList """
    return SaveList(self._axstack.as_list())


def return_save_list(func):
    """ a decorator to wrap the output of a function as a SaveList """
    def wrap(*args, **kwargs):
        return SaveList(func(*args, **kwargs))
    return wrap


def swallow_get_exceptions():
    """ replace lists with lists that return dummy objects when items are not present.
        this is to ensure that the pylustrator generated code does not fail, even if the user removes some elements
        from the figure.
    """
    Figure._get_axes = get_axes
    Figure.axes = property(fget=get_axes)
    Figure.ax_dict = SaveListDescriptor("ax_dict")
    _AxesBase.texts = SaveListDescriptor("texts")
    _AxesBase.lines = SaveListDescriptor("lines")
    _AxesBase.patches = SaveListDescriptor("patches")
    Axis.get_minor_ticks = return_save_list(Axis.get_minor_ticks)
    Axis.get_major_ticks = return_save_list(Axis.get_major_ticks)
    l = _AxesBase.get_legend
    def get_legend(*args, **kwargs):
        leg = l(*args, **kwargs)
        if leg is None:
            return Dummy()
        return leg

    _AxesBase.get_legend = get_legend