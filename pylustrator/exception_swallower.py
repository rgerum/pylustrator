from matplotlib.figure import Figure
from matplotlib.axes._base import _AxesBase
from matplotlib.axis import Axis


class Dummy:
    def __getattr__(self, item):
        return Dummy()

    def __call__(self, *args, **kwargs):
        return Dummy()

    def __getitem__(self, item):
        return Dummy()


class SaveList(list):
    def __init__(self, target):
        list.__init__(self, target)

    def __getitem__(self, item):
        try:
            return list.__getitem__(self, item)
        except IndexError:
            return Dummy()


class SaveDict(dict):
    def __init__(self, target):
        dict.__init__(self, target)

    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            return Dummy()


class SaveTuple(tuple):
    def __init__(self, target):
        tuple.__init__(self, target)

    def __getitem__(self, item):
        try:
            return tuple.__getitem__(self, item)
        except IndexError:
            return Dummy()


class SaveListDescriptor:
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
    return SaveList(self._axstack.as_list())


def return_save_list(func):
    def wrap(*args, **kwargs):
        return SaveList(func(*args, **kwargs))
    return wrap


def swallow_get_exceptions():
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