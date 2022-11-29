import unittest
import numpy as np
import re
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from typing import Any


def ensure_list(obj, count=1):
    if isinstance(obj, list):
        return obj
    else:
        return [obj]*count


class TestFits(unittest.TestCase):

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
plt.bar(0, np.mean(a))
plt.bar(1, np.mean(b))

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

    def test_moveFigure(self):
        # get the figure
        fig, text = self.run_plot_script()

        # and select and move the axes
        self.move_element((-1, 0), fig.axes[0])

        # find the saved string and check the numbers
        line, (args, kwargs) = self.check_line_in_file("plt.figure(1).axes[0].set_position(")
        np.testing.assert_almost_equal(args[0], [0.123438, 0.11, 0.227941, 0.77], 2,
                                       "Figure movement not correctly written to file")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the axes is at the right position
        np.testing.assert_almost_equal(np.array(fig.axes[0].get_position()), [[0.123438, 0.11], [0.351379, 0.88]], 2,
                                       "Saved axes not loaded correctly")

        # don't move it and save the result
        self.move_element((0, 0), fig.axes[0])

        # the output should still be the same
        self.assertEqual(text, self.get_script_text(), "Saved differently")

    def assertEqualStringOrArray(self, first, second, msg) -> None:
        if isinstance(first, str) or first is None:
            self.assertEqual(first, second, msg)
        else:
            np.testing.assert_almost_equal(first, second, 3, msg)

    def change_property(self, property_name, value, call, get_obj, line_command, test_run, value2: Any = "undefined"):
        if value2 == "undefined":
            value2 = value
        if isinstance(get_obj, list):
            return self.change_property2(property_name, value, call, get_obj, line_command, test_run,
                                         value2_list=value2)
        fig = self.fig
        obj = get_obj()
        fig.figure_dragger.select_element(obj)

        # get current value
        current_value = getattr(get_obj(), f"get_{property_name}")()

        # set the text to bold
        call(obj)
        fig.change_tracker.save()

        # test if the text has the right weight
        self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(),
                                      f"Property '{property_name}' not set correctly. [{test_run}]")

        # test undo and redo
        fig.window.undo()
        self.assertEqualStringOrArray(current_value, getattr(get_obj(), f"get_{property_name}")(),
                                      f"Property '{property_name}' undo failed. [{test_run}]")
        fig.window.redo()
        self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(),
                                      f"Property '{property_name}' redo failed. [{test_run}]")

        # find the saved string and check the numbers
        line, (args, kwargs) = self.check_line_in_file(line_command)
        if line_command.endswith(".text("):
            if property_name == "position":
                kwargs["position"] = args[:2]
            if property_name == "text":
                kwargs["text"] = args[2]
        self.assertEqualStringOrArray(value2, kwargs.get(property_name),
                                      f"Property '{property_name}' not saved correctly. [{test_run}]")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the text has the right weight
        self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(),
                                      f"Property '{property_name}' not restored correctly. [{test_run}]")

        # select the text
        fig.figure_dragger.select_element(get_obj())
        # don't move it and save the result
        self.move_element((0, 0), get_obj())

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

    def test_text_properties_axes_existing(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = lambda: fig.axes[0].texts[0]
        line_command = "plt.figure(1).axes[0].texts[0].set("
        test_run = "Change existing text in axes."
        self.check_text_properties(get_text, line_command, test_run, 0.4931, 0.4979)

    def test_text_properties_axes_new(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.axes[0].texts[-1]
        line_command = "plt.figure(1).axes[0].text("
        test_run = "Change new text in axes."

        self.check_text_properties(get_text, line_command, test_run, 0.4931, 0.4979)

    def test_text_properties_figure_existing(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = lambda: fig.texts[-1]
        line_command = "plt.figure(1).texts[0].set("
        test_run = "Change existing text in Figure."

        self.check_text_properties(get_text, line_command, test_run, 0.4984, 0.4979)

    def test_text_properties_figure_new(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig)
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.texts[-1]
        line_command = "plt.figure(1).text("
        test_run = "Change new text in Figure."

        self.check_text_properties(get_text, line_command, test_run, 0.4984, 0.4979)

    def test_text_property_together(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = [lambda: fig.axes[0].texts[0], lambda: fig.axes[0].texts[-1]]
        line_command = ["plt.figure(1).axes[0].texts[0].set(", "plt.figure(1).axes[0].text("]
        test_run = "Change new text in axes."

        self.check_text_properties(get_text, line_command, test_run, 0.493, 0.497)

    def test_text_alignment(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = [lambda: fig.axes[0].texts[0], lambda: fig.axes[0].texts[1]]
        line_command = ["plt.figure(1).axes[0].texts[0].set(", "plt.figure(1).axes[0].text("]
        test_run = "Change new text in axes."

        # align left
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])

        self.change_property2("position", [(0.2, 0.2), (0.2, 0.6)],
                              lambda _: fig.window.input_align.buttons[0].clicked.emit(0), get_text, line_command,
                              test_run)

        # align center
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])

        self.change_property2("position", [(0.55, 0.2), (0.472, 0.6)],
                              lambda _: fig.window.input_align.buttons[1].clicked.emit(0), get_text, line_command,
                              test_run)

        # align right
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])

        self.change_property2("position", [(0.834, 0.2), (0.6, 0.6)],
                              lambda _: fig.window.input_align.buttons[2].clicked.emit(0), get_text, line_command,
                              test_run)

        # align top
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])

        self.change_property2("position", [(0.2, 0.6), (0.6, 0.6)],
                              lambda _: fig.window.input_align.buttons[4].clicked.emit(0), get_text, line_command,
                              test_run)

        # align center
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])

        self.change_property2("position", [(0.2, 0.404), (0.6, 0.404)],
                              lambda _: fig.window.input_align.buttons[5].clicked.emit(0), get_text, line_command,
                              test_run)

        # align bottom
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])

        self.change_property2("position", [(0.2, 0.2), (0.6, 0.2)],
                              lambda _: fig.window.input_align.buttons[6].clicked.emit(0), get_text, line_command,
                              test_run)

    def test_text_distribute(self):
        # get the figure
        fig, text = self.run_plot_script()

        # create two additional text so that we have 3 in total
        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()
        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = [lambda: fig.axes[0].texts[0], lambda: fig.axes[0].texts[1]]
        line_command = ["plt.figure(1).axes[0].texts[0].set(", "plt.figure(1).axes[0].text(", "plt.figure(1).axes[0].text("]
        test_run = "Change new text in axes."

        # distribute X
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.axes[0].texts[2].set_position([0.5, 0.5])

        self.change_property2("position", [(0.2, 0.2), (1.0301, 0.6), (0.5, 0.5)],
                              lambda _: fig.window.input_align.buttons[3].clicked.emit(0), get_text, line_command,
                              test_run)

        # distribute Y
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.axes[0].texts[2].set_position([0.5, 0.5])

        self.change_property2("position", [(0.2, 0.2), (0.6, 0.6460), (0.5, 0.5)],
                              lambda _: fig.window.input_align.buttons[7].clicked.emit(0), get_text, line_command,
                              test_run)

    def check_text_properties(self, get_text, line_command, test_run, x, y):
        fig = self.fig
        self.change_property("position", (x, 0.5), lambda _: self.move_element((-1, 0)), get_text, line_command, test_run)
        self.change_property("position", (0.5, 0.5), lambda _: self.move_element((1, 0)), get_text, line_command, test_run)
        self.change_property("position", (0.5, y), lambda _: self.move_element((0, -1)), get_text, line_command, test_run)
        self.change_property("position", (0.5, 0.5), lambda _: self.move_element((0, 1)), get_text, line_command, test_run)
        self.change_property("position", (0.2, 0.5), lambda _: fig.window.input_size.input_position.valueChangedX.emit(0.2), get_text, line_command, test_run)
        self.change_property("position", (0.2, 0.2), lambda _: fig.window.input_size.input_position.valueChangedY.emit(0.2), get_text, line_command, test_run)
        self.change_property("weight", "bold", lambda _: fig.window.input_properties.input_font_properties.button_bold.clicked.emit(True), get_text, line_command, test_run)
        self.change_property("weight", "normal", lambda _: fig.window.input_properties.input_font_properties.button_bold.clicked.emit(False), get_text, line_command, test_run, value2=None)
        self.change_property("style", "italic", lambda _: fig.window.input_properties.input_font_properties.button_italic.clicked.emit(True), get_text, line_command, test_run)
        self.change_property("style", "normal", lambda _: fig.window.input_properties.input_font_properties.button_italic.clicked.emit(False), get_text, line_command, test_run, value2=None)
        self.change_property("ha", "left", lambda _: fig.window.input_properties.input_font_properties.buttons_align[0].clicked.emit(True), get_text, line_command, test_run, value2=None)
        self.change_property("ha", "center", lambda _: fig.window.input_properties.input_font_properties.buttons_align[1].clicked.emit(True), get_text, line_command, test_run)
        self.change_property("ha", "right", lambda _: fig.window.input_properties.input_font_properties.buttons_align[2].clicked.emit(True), get_text, line_command, test_run)
        self.change_property("color", "#FF0000", lambda _: fig.window.input_properties.input_font_properties.button_color.valueChanged.emit("#FF0000"), get_text, line_command, test_run)
        self.change_property("fontsize", 8, lambda _: fig.window.input_properties.input_font_properties.font_size.valueChanged.emit(8), get_text, line_command, test_run)
        self.change_property("text", "update", lambda _: fig.window.input_properties.input_text.setText("update", signal=True), get_text, line_command, test_run)
        self.change_property("rotation", 45, lambda _: fig.window.input_properties.input_rotation.setValue(45, signal=True), get_text, line_command, test_run)
