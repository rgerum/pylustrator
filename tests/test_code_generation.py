import unittest
import numpy as np
import re
from pathlib import Path
from matplotlib import _pylab_helpers


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

    def test_moveFigure(self):
        with open(self.filename, "rb") as fp:
            text = fp.read()
        exec(compile(text, self.filename, 'exec'), globals())

        for figure in _pylab_helpers.Gcf.figs:
            figure = _pylab_helpers.Gcf.figs[figure].canvas.figure
            figure.figure_dragger.select_element(figure.axes[0])

            figure.selection.start_move()
            figure.selection.addOffset((-1, 0), figure.selection.dir)
            figure.selection.end_move()
            figure.change_tracker.save()

        with self.filename.open("r") as fp:
            in_block = False
            found = False
            block = ""
            for line in fp:
                if in_block is True:
                    block += line
                    if line.startswith("plt.figure(1).axes[0].set_position("):
                        data = re.match(r"plt\.figure\(1\)\.axes\[0\]\.set_position\(\[([\.\d]*), ([\.\d]*), ([\.\d]*), ([\.\d]*)]\)", line).groups()
                        if np.all([np.abs(float(d1)-d2)<0.2 for d1, d2 in zip(data, [0.12, 0.11, 0.23, 0.77])]):
                            found = True
                if line.startswith("#% start: automatic generated code from pylustrator"):
                    in_block = True
                if line.startswith("#% end: automatic generated code from pylustrator"):
                    in_block = False

        self.assertTrue(found, "Figure movement not correctly written to file")
