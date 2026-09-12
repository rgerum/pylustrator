"""A figure legend given an anchor box, and an axes title, must move by the drag.

Two placements matplotlib owns and re-applies after pylustrator has written a
position:

* a legend anchored with `bbox_to_anchor` is placed at
  `bbox.x0 + bbox.width * loc[0]`, so an anchor passed as a *point* has zero
  width and every location maps to one pixel. The selection followed the drag
  and the legend did not move at all.
* an axes title's y is recomputed on every draw by `_update_title_position`
  unless the position was set by hand, so a dragged title snapped back on the
  next redraw.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

import matplotlib
import numpy as np

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402 -- the backend must be chosen first

from base_test_class import BaseTest  # noqa: E402


class TestAnchoredLegendAndTitle(BaseTest):
    def _figure(self):
        import pylustrator
        from pylustrator import QtGuiDrag

        pylustrator.start()
        fig = plt.figure(figsize=(6, 4))
        axes = fig.subfigures(1, 1).add_subplot()
        axes.plot([0, 1], [0, 1], label="a line")
        axes.set_title("a title")
        # The anchor a paper figure uses to place one legend for the whole
        # canvas, and the case that did not move.
        fig.legend(loc="lower left", bbox_to_anchor=(0.1, 0.02))
        fig.canvas.draw()
        QtGuiDrag.pyl_show(hide_window=True)
        fig.canvas.draw()
        self.fig = fig
        return fig, axes

    @staticmethod
    def _corner(artist):
        box = artist.get_window_extent()
        return np.array([box.x0, box.y0])

    def test_dragging_an_anchored_figure_legend_moves_it(self):
        fig, _ = self._figure()
        legend = fig.legends[0]
        before = self._corner(legend.get_frame())

        self.move_element((25, 18), legend)
        fig.canvas.draw()

        np.testing.assert_allclose(
            self._corner(legend.get_frame()) - before, np.array([25.0, 18.0]), atol=1.0
        )
        plt.close(fig)

    def test_dragging_a_title_survives_the_next_draw(self):
        fig, axes = self._figure()
        before = self._corner(axes.title)

        self.move_element((0, 14), axes.title)
        fig.canvas.draw()
        # The redraw that used to undo it.
        fig.canvas.draw()

        np.testing.assert_allclose(
            self._corner(axes.title) - before, np.array([0.0, 14.0]), atol=1.0
        )
        plt.close(fig)


if __name__ == "__main__":
    unittest.main()
