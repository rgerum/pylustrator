import unittest
import numpy as np
import re
from pathlib import Path
from matplotlib import _pylab_helpers
import matplotlib.pyplot as plt


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
                        def grab_args(*args, **kwargs):
                            return args, kwargs

                        args = re.match(re.escape(line_start)+r"(.*)\)", line).groups()[0]
                        return line, eval(f"grab_args({args})")
                if line.startswith("#% start: automatic generated code from pylustrator"):
                    in_block = True
                if line.startswith("#% end: automatic generated code from pylustrator"):
                    in_block = False

    def move_element(self, element, offset):
        fig = self.fig
        # select the text
        fig.figure_dragger.select_element(element)
        # don't move it and save the result
        fig.selection.start_move()
        fig.selection.addOffset(offset, fig.selection.dir)
        fig.selection.end_move()
        fig.change_tracker.save()

    def test_moveFigure(self):
        # get the figure
        fig, text = self.run_plot_script()

        # and select and move the axes
        self.move_element(fig.axes[0], (-1, 0))

        # find the saved string and check the numbers
        line, (args, kwargs) = self.check_line_in_file("plt.figure(1).axes[0].set_position(")
        np.testing.assert_almost_equal(args[0], [0.123438, 0.11, 0.227941, 0.77], 2, "Figure movement not correctly written to file")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the axes is at the right position
        np.testing.assert_almost_equal(np.array(fig.axes[0].get_position()), [[0.123438, 0.11], [0.351379, 0.88]], 2, "Saved axes not loaded correctly")

        # don't move it and save the result
        self.move_element(fig.axes[0], (0, 0))

        # the output should still be the same
        self.assertEqual(text, self.get_script_text(), "Saved differently")

    def assertEqualStringOrArray(self, first, second, msg) -> None:
        if isinstance(first, str) or first is None:
            self.assertEqual(first, second, msg)
        else:
            np.testing.assert_almost_equal(first, second, 2, msg)

    def change_property(self, property_name, value, value2, call, get_obj, line_command, test_run):
        fig = self.fig
        obj = get_obj()
        fig.figure_dragger.select_element(obj)

        # get current value
        current_value = getattr(get_obj(), f"get_{property_name}")()

        # set the text to bold
        call(obj)
        fig.change_tracker.save()

        # test if the text has the right weight
        self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(), f"Property '{property_name}' not set correctly. [{test_run}]")

        # test undo and redo
        fig.window.undo()
        self.assertEqualStringOrArray(current_value, getattr(get_obj(), f"get_{property_name}")(), f"Property '{property_name}' undo failed. [{test_run}]")
        fig.window.redo()
        self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(), f"Property '{property_name}' redo failed. [{test_run}]")

        # find the saved string and check the numbers
        line, (args, kwargs) = self.check_line_in_file(line_command)
        if line_command.endswith(".text("):
            if property_name == "position":
                kwargs["position"] = args[:2]
            if property_name == "text":
                kwargs["text"] = args[2]
        self.assertEqualStringOrArray(value2, kwargs.get(property_name), f"Property '{property_name}' not saved correctly. [{test_run}]")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the text has the right weight
        self.assertEqualStringOrArray(value, getattr(get_obj(), f"get_{property_name}")(), f"Property '{property_name}' not restored correctly. [{test_run}]")

        # select the text
        fig.figure_dragger.select_element(get_obj())
        # don't move it and save the result
        self.move_element(get_obj(), (0, 0))

        # the output should still be the same
        self.assertEqual(text, self.get_script_text(), f"Saved differently. Property '{property_name}'. [{test_run}]")

    def test_text_properties_axes_existing(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = lambda: fig.axes[0].texts[0]
        line_command = "plt.figure(1).axes[0].texts[0].set("
        test_run = "Change existing text in axes."
        self.check_text_properties(get_text, line_command, test_run)

    def test_text_properties_axes_new(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.axes[0].texts[-1]
        line_command = "plt.figure(1).axes[0].text("
        test_run = "Change new text in axes."

        self.check_text_properties(get_text, line_command, test_run)

    def test_text_properties_figure_existing(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = lambda: fig.texts[-1]
        line_command = "plt.figure(1).texts[0].set("
        test_run = "Change existing text in Figure."

        self.check_text_properties(get_text, line_command, test_run)

    def test_text_properties_figure_new(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig)
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.texts[-1]
        line_command = "plt.figure(1).text("
        test_run = "Change new text in Figure."

        self.check_text_properties(get_text, line_command, test_run)

    def check_text_properties(self, get_text, line_command, test_run):
        fig = self.fig
        self.change_property("position", (0.4849, 0.5), (0.4849, 0.5), lambda obj: self.move_element(obj, (-1, 0)), get_text, line_command, test_run)
        self.change_property("position", (0.5, 0.5), (0.5, 0.5), lambda obj: self.move_element(obj, (1, 0)), get_text, line_command, test_run)
        self.change_property("position", (0.5, 0.4881), (0.5, 0.4881), lambda obj: self.move_element(obj, (0, -1)), get_text, line_command, test_run)
        self.change_property("position", (0.5, 0.5), (0.5, 0.5), lambda obj: self.move_element(obj, (0, 1)), get_text, line_command, test_run)
        self.change_property("position", (0.2, 0.5), (0.2, 0.5), lambda _: fig.window.input_size.input_position.valueChangedX.emit(0.2), get_text, line_command, test_run)
        self.change_property("position", (0.2, 0.2), (0.2, 0.2), lambda _: fig.window.input_size.input_position.valueChangedY.emit(0.2), get_text, line_command, test_run)
        self.change_property("weight", "bold", "bold", lambda _: fig.window.input_properties.input_font_properties.button_bold.clicked.emit(True), get_text, line_command, test_run)
        self.change_property("weight", "normal", None, lambda _: fig.window.input_properties.input_font_properties.button_bold.clicked.emit(False), get_text, line_command, test_run)
        self.change_property("style", "italic", "italic", lambda _: fig.window.input_properties.input_font_properties.button_italic.clicked.emit(True), get_text, line_command, test_run)
        self.change_property("style", "normal", None, lambda _: fig.window.input_properties.input_font_properties.button_italic.clicked.emit(False), get_text, line_command, test_run)
        self.change_property("ha", "left", None, lambda _: fig.window.input_properties.input_font_properties.buttons_align[0].clicked.emit(True), get_text, line_command, test_run)
        self.change_property("ha", "center", "center", lambda _: fig.window.input_properties.input_font_properties.buttons_align[1].clicked.emit(True), get_text, line_command, test_run)
        self.change_property("ha", "right", "right", lambda _: fig.window.input_properties.input_font_properties.buttons_align[2].clicked.emit(True), get_text, line_command, test_run)
        self.change_property("color", "#FF0000", "#FF0000", lambda _: fig.window.input_properties.input_font_properties.button_color.valueChanged.emit("#FF0000"), get_text, line_command, test_run)
        self.change_property("fontsize", 8, 8, lambda _: fig.window.input_properties.input_font_properties.font_size.valueChanged.emit(8), get_text, line_command, test_run)
        self.change_property("text", "update", "update", lambda _: fig.window.input_properties.input_text.setText("update", signal=True), get_text, line_command, test_run)
        self.change_property("rotation", 45, 45, lambda _: fig.window.input_properties.input_rotation.setValue(45, signal=True), get_text, line_command, test_run)

