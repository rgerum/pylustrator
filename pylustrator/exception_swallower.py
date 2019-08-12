from matplotlib.figure import Figure
from matplotlib.axes._base import _AxesBase
from matplotlib.axis import Axis, YAxis


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


class SaveListDescriptor:
    def __set__(self, instance, value):
        self.value = value

    def __get__(self, instance, owner):
        return SaveList(self.value)


def get_axes(self):
    return SaveList(self._axstack.as_list())


def return_save_list(func):
    def wrap(*args, **kwargs):
        return SaveList(func(*args, **kwargs))
    return wrap


def swallow_get_exceptions():
    Figure._get_axes = get_axes
    Figure.axes = property(fget=get_axes)
    Figure.ax_dict = SaveListDescriptor()
    #_AxesBase.texts = SaveListDescriptor()
    #_AxesBase.lines = SaveListDescriptor()
    #_AxesBase.patches = SaveListDescriptor()
    Axis.get_minor_ticks = return_save_list(Axis.get_minor_ticks)
    Axis.get_major_ticks = return_save_list(Axis.get_major_ticks)
