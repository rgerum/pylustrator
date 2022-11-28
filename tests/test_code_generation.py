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

plt.figure(1)
plt.subplot(131)
plt.plot(t, y)
plt.text(0.5, 0.5, "new")

plt.subplot(132)
plt.plot(a, b, "o")

plt.subplot(133)
plt.bar(0, np.mean(a))
plt.bar(1, np.mean(b))

# show the plot in a pylustrator window
plt.show(hide_window=True)
    """)

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
                        return line
                if line.startswith("#% start: automatic generated code from pylustrator"):
                    in_block = True
                if line.startswith("#% end: automatic generated code from pylustrator"):
                    in_block = False

    def print_saved_block(self):
        with self.filename.open("r") as fp:
            in_block = False
            block = ""
            for line in fp:
                if in_block is True:
                    block += line
                if line.startswith("#% start: automatic generated code from pylustrator"):
                    in_block = True
                if line.startswith("#% end: automatic generated code from pylustrator"):
                    in_block = False
            print(block)

    def match_numbers(self, regex, line):
        groups = re.match(regex, line).groups()
        data = [float(s) for s in groups]
        return data

    def test_moveFigure(self):
        with open(self.filename, "rb") as fp:
            text = fp.read()
        exec(compile(text, self.filename, 'exec'), globals())

        # get the figure
        fig = plt.gcf()
        ax = fig.axes[0]
        # and select the axes
        fig.figure_dragger.select_element(ax)

        # move the axes and save
        fig.selection.start_move()
        fig.selection.addOffset((-1, 0), fig.selection.dir)
        fig.selection.end_move()
        fig.change_tracker.save()

        # find the saved string and check the numbers
        line = self.check_line_in_file("plt.figure(1).axes[0].set_position(")
        data = self.match_numbers(r"plt\.figure\(1\)\.axes\[0\]\.set_position\(\[([\.\d]*), ([\.\d]*), ([\.\d]*), ([\.\d]*)]\)", line)
        np.testing.assert_almost_equal(data, [0.123438, 0.11, 0.227941, 0.77], 2, "Figure movement not correctly written to file")

        # run the file again
        with open(self.filename, "rb") as fp:
            text = fp.read()
        exec(compile(text, self.filename, 'exec'), globals())

        # test if the axes is at the right position
        fig = plt.gcf()
        ax = fig.axes[0]
        np.testing.assert_almost_equal(np.array(ax.get_position()), np.array([[0.123438, 0.11], [0.351379, 0.88]]), 2, "Saved axes not loaded correctly")

        # select the axes
        fig.figure_dragger.select_element(ax)
        # don't move it and save the result
        fig.selection.start_move()
        fig.selection.addOffset((0, 0), fig.selection.dir)
        fig.selection.end_move()
        fig.change_tracker.save()

        # the output should still be the same
        with open(self.filename, "rb") as fp:
            text2 = fp.read()

        self.assertEqual(text, text2, "Saved differently")

    def test_moveText(self):
        with open(self.filename, "rb") as fp:
            text = fp.read()
        exec(compile(text, self.filename, 'exec'), globals())

        # get the figure
        fig = plt.gcf()
        t = fig.axes[0].texts[0]
        # and select the axes
        fig.figure_dragger.select_element(t)

        # move the axes and save
        fig.selection.start_move()
        fig.selection.addOffset((-1, 0), fig.selection.dir)
        fig.selection.end_move()
        fig.change_tracker.save()

        # find the saved string and check the numbers
        line = self.check_line_in_file("plt.figure(1).axes[0].texts[0].set(")
        data = self.match_numbers(r".*set\(.*position=\(([\.\d]*), ([\.\d]*)\)", line)
        np.testing.assert_almost_equal(data, [0.48, 0.5], 2, "Text movement not correctly written to file")

        # run the file again
        with open(self.filename, "rb") as fp:
            text = fp.read()
        exec(compile(text, self.filename, 'exec'), globals())

        # test if the axes is at the right position
        fig = plt.gcf()
        t = fig.axes[0].texts[0]
        np.testing.assert_almost_equal(np.array(t.get_position()), np.array([0.48, 0.5]), 2, "Saved axes not loaded correctly")

        # select the axes
        fig.figure_dragger.select_element(t)
        # don't move it and save the result
        fig.selection.start_move()
        fig.selection.addOffset((0, 0), fig.selection.dir)
        fig.selection.end_move()
        fig.change_tracker.save()

        # the output should still be the same
        with open(self.filename, "rb") as fp:
            text2 = fp.read()

        self.assertEqual(text, text2, "Saved differently")
