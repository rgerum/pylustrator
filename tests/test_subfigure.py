"""Artists drawn on a subfigure must be selectable.

`Figure.subfigures` is the standard way to build a multi-panel publication
figure, and an artist placed on one reports the subfigure, not the canvas, as
its figure. The target wrapper asked for a `Figure`, so on such a figure every
click was turned away with "TargetWrapper needs a figure" and nothing could be
selected or moved.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

import matplotlib
import numpy as np

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402 -- the backend must be chosen first

from base_test_class import BaseTest  # noqa: E402


class TestSubFigure(BaseTest):
    def _figure(self):
        import pylustrator
        from pylustrator import QtGuiDrag

        pylustrator.start()
        fig = plt.figure(figsize=(4, 3))
        panel = fig.subfigures(1, 1)
        axes = panel.add_subplot()
        axes.plot([0, 1], [0, 1], label="a line")
        axes.legend()
        axes.set_title("a title")
        axes.set_xlabel("x")
        panel.text(0.02, 0.95, "a")
        fig.canvas.draw()
        QtGuiDrag.pyl_show(hide_window=True)
        fig.canvas.draw()
        self.fig = fig
        return fig, panel, axes

    @staticmethod
    def _corner(artist):
        box = artist.get_window_extent()
        return np.array([box.x0, box.y0])

    def test_every_artist_on_a_subfigure_can_be_selected(self):
        fig, panel, axes = self._figure()
        letter = panel.texts[0]

        for artist, movable in (
            (axes, True),
            (axes.title, True),
            (axes.xaxis.get_label(), True),
            (axes.get_legend(), True),
            (letter, True),
            # A line has no position the editor can write, so it is selected
            # but never becomes a target -- on a plain figure just the same.
            (axes.lines[0], False),
        ):
            with self.subTest(artist=type(artist).__name__, movable=movable):
                # The editor's own path: add_target() wraps the artist and
                # reads its positions, which is what used to raise.
                fig.figure_dragger.select_element(artist)
                selected = [target.target for target in fig.selection.targets]
                if movable:
                    self.assertIn(artist, selected)
                else:
                    self.assertNotIn(artist, selected)
        plt.close(fig)

    def test_an_artist_on_a_subfigure_moves_by_the_drag(self):
        fig, panel, _ = self._figure()
        letter = panel.texts[0]
        before = self._corner(letter)

        self.move_element((12, -9), letter)
        fig.canvas.draw()

        np.testing.assert_allclose(
            self._corner(letter) - before, np.array([12.0, -9.0]), atol=1.0
        )
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
