import unittest
import numpy as np
import re
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent, KeyEvent
from typing import Any


def ensure_list(obj, count=1):
    if isinstance(obj, list):
        return obj
    else:
        return [obj]*count


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.filename = Path(self.id().split(".")[-1] + ".py")
        with self.filename.open("w") as fp:
            fp.write("""
import matplotlib.pyplot as plt
import numpy as np

# now import pylustrator
import pylustrator

# activate pylustrator
pylustrator.start()

# build plots as you normally would
np.random.seed(1)
t = np.arange(0.0, 2, 0.001)
y = 2 * np.sin(np.pi * t)
a, b = np.random.normal(loc=(5., 3.), scale=(2., 4.), size=(100,2)).T
b += a

fig = plt.figure(1)
plt.clf()
fig.text(0.5, 0.5, "new", transform=plt.figure(1).transFigure)
plt.subplot(131)
plt.plot(t, y)
plt.text(0.5, 0.5, "new", transform=plt.figure(1).axes[0].transAxes)

plt.subplot(132)
plt.plot(a, b, "o")

plt.subplot(133)
plt.bar(0, np.mean(a), label="a")
plt.bar(1, np.mean(b), label="b")

# show the plot in a pylustrator window
plt.show(hide_window=True)
    """)

    def get_script_text(self):
        with open(self.filename, "rb") as fp:
            text = fp.read()
        return text

    def run_plot_script(self):
        text = self.get_script_text()
        exec(compile(text, self.filename, 'exec'), globals())
        self.fig = plt.gcf()
        return plt.gcf(), text

    def tearDown(self):
        self.filename.unlink()
        tmp_file = Path(str(self.filename) + ".tmp")
        if tmp_file.exists():
            tmp_file.unlink()

    def check_line_in_file(self, line_start):
        with self.filename.open("r") as fp:
            in_block = False
            block = ""
            for line in fp:
                if in_block is True:
                    block += line
                    if line.startswith(line_start):
                        # noinspection PyUnusedLocal
                        def grab_args(*args, **kwargs):
                            return args, kwargs

                        arguments = re.match(re.escape(line_start)+r"(.*)\)", line).groups()[0]
                        return line, eval(f"grab_args({arguments})")
                if line.startswith("#% start: automatic generated code from pylustrator"):
                    in_block = True
                if line.startswith("#% end: automatic generated code from pylustrator"):
                    in_block = False

    def move_element(self, offset, element=None):
        fig = self.fig
        # select the text
        if element is not None:
            fig.figure_dragger.select_element(element)
        # don't move it and save the result
        fig.selection.start_move()
        fig.selection.has_moved = True
        fig.selection.addOffset(offset, fig.selection.dir)
        fig.selection.end_move()
        fig.change_tracker.save()

    def assertEqualStringOrArray(self, first, second, msg) -> None:
        if isinstance(first, str) or first is None:
            self.assertEqual(first, second, msg)
        else:
            np.testing.assert_almost_equal(first, second, 3, msg)

    def change_property(self, property_name, value, call, get_obj, line_command, test_run, value2: Any = "undefined", get_function=None):
        if value2 == "undefined":
            value2 = value
        if isinstance(get_obj, list):
            return self.change_property2(property_name, value, call, get_obj, line_command, test_run,
                                         value2_list=value2)

        if get_function is None:
            get_function = getattr(get_obj(), f"get_{property_name}")

        fig = self.fig
        obj = get_obj()
        fig.figure_dragger.select_element(obj)

        # get current value
        current_value = get_function()

        # set the text to bold
        call(obj)
        fig.change_tracker.save()

        # test if the text has the right weight
        self.assertEqualStringOrArray(value, get_function(),
                                      f"Property '{property_name}' not set correctly. [{test_run}]")

        # test undo and redo
        fig.window.undo()
        self.assertEqualStringOrArray(current_value, get_function(),
                                      f"Property '{property_name}' undo failed. [{test_run}]")
        fig.window.redo()
        self.assertEqualStringOrArray(value, get_function(),
                                      f"Property '{property_name}' redo failed. [{test_run}]")

        # find the saved string and check the numbers
        try:
            line, (args, kwargs) = self.check_line_in_file(line_command)
            # if the task is to delete then it is now allowed to find the text
            if property_name == "visible" and line_command.endswith(".text("):
                raise TypeError
        except TypeError as err:
            if property_name == "visible" and line_command.endswith(".text("):
                kwargs = dict(visible=False)
            else:
                raise err
        if line_command.endswith(".text("):
            if property_name == "position":
                kwargs["position"] = args[:2]
            if property_name == "text":
                kwargs["text"] = args[2]
        if property_name == "xlim":
            kwargs["xlim"] = args[:2]
        if property_name == "ylim":
            kwargs["ylim"] = args[:2]
        if property_name == "xlabel":
            kwargs["xlabel"] = kwargs["text"]
        if property_name == "ylabel":
            kwargs["ylabel"] = kwargs["text"]
        if property_name == "grid":
            kwargs["grid"] = args[0]
        if property_name == "despine":
            kwargs["despine"] = args[0]
        self.assertEqualStringOrArray(value2, kwargs.get(property_name),
                                      f"Property '{property_name}' not saved correctly. [{test_run}]")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the text has the right weight
        try:
            self.assertEqualStringOrArray(value, get_function(),
                                          f"Property '{property_name}' not restored correctly. [{test_run}]")
            # when the task is to delete then finding it is an error
            if property_name == "visible" and line_command.endswith(".text("):
                raise IndexError

            # select the text
            fig.figure_dragger.select_element(get_obj())
            # don't move it and save the result
            self.move_element((0, 0), get_obj())
        except IndexError as err:
            #  ... and not finding it is good
            if property_name == "visible" and line_command.endswith(".text("):
                pass
            else:
                raise err

        # the output should still be the same
        self.assertEqual(text, self.get_script_text(), f"Saved differently. Property '{property_name}'. [{test_run}]")

    def change_property2(self, property_name_list, value_list, call, get_obj_list, line_command_list,
                         test_run, value2_list="undefined", show=False):
        if value2_list == "undefined":
            value2_list = value_list
        get_obj_list = ensure_list(get_obj_list)
        property_name_list = ensure_list(property_name_list, len(get_obj_list))
        value_list = ensure_list(value_list, len(get_obj_list))
        value2_list = ensure_list(value2_list, len(get_obj_list))
        line_command_list = ensure_list(line_command_list, len(get_obj_list))

        fig = self.fig
        # we need the draw here so that the bounding boxes of the texts are right
        fig.canvas.draw()

        for index, get_obj in enumerate(get_obj_list):
            if index == 0:
                fig.figure_dragger.select_element(get_obj())
            else:
                fig.figure_dragger.select_element(get_obj(), MouseEvent("select", fig.canvas, 0, 0, key="shift"))

        # get current value
        current_values = [getattr(get_obj(), f"get_{property_name}")()
                          for get_obj, property_name in zip(get_obj_list, property_name_list)]

        # set the text to bold
        call([get_obj() for get_obj in get_obj_list])
        fig.change_tracker.save()

        # test if the text has the right weight
        for get_obj, property_name, value in zip(get_obj_list, property_name_list, value_list):
            self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(),
                                          f"Property '{property_name}' not set correctly. [{test_run}]")

        # test undo and redo
        fig.window.undo()
        for get_obj, property_name, current_value in zip(get_obj_list, property_name_list, current_values):
            self.assertEqualStringOrArray(current_value, getattr(get_obj(), f"get_{property_name}")(),
                                          f"Property '{property_name}' undo failed. [{test_run}]")
        fig.window.redo()
        for get_obj, property_name, value in zip(get_obj_list, property_name_list, value_list):
            self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(),
                                          f"Property '{property_name}' redo failed. [{test_run}]")

        # find the saved string and check the numbers
        for command, value2, property_name in zip(line_command_list, value2_list, property_name_list):
            line, (args, kwargs) = self.check_line_in_file(command)
            if command.endswith(".text("):
                if property_name == "position":
                    kwargs["position"] = args[:2]
                if property_name == "text":
                    kwargs["text"] = args[2]
            self.assertEqualStringOrArray(value2, kwargs.get(property_name),
                                          f"Property '{property_name}' not saved correctly. [{test_run}]")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the text has the right weight
        for get_obj, property_name, value in zip(get_obj_list, property_name_list, value_list):
            self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(),
                                          f"Property '{property_name}' not set correctly. [{test_run}]")

        # select the text
        for get_obj in get_obj_list:
            # don't move it and save the result
            self.move_element((0, 0), get_obj())

        # the output should still be the same
        self.assertEqual(text, self.get_script_text(),
                         f"Saved differently. Property '{property_name_list}'. [{test_run}]")