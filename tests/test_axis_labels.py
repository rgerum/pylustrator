"""An axis label must stay where it is put, and move by the drag.

An axis label is placed by its labelpad, which matplotlib applies away from the
axis. The offset the wrapper stored for that had the opposite sign, so writing a
label back at the position it already held returned the pad negated -- 4 points
became -4 -- and the label jumped through the axis to the other side.

Which way the pad moves the label depends on the side it sits on, so a label
moved to the top or the right is covered here too.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest

import matplotlib
import numpy as np

matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402 -- the backend must be chosen first

from base_test_class import BaseTest  # noqa: E402
from pylustrator.snap import TargetWrapper  # noqa: E402


class TestAxisLabels(BaseTest):
    def _figure(self, xside="bottom", yside="left"):
        import pylustrator
        from pylustrator import QtGuiDrag

        pylustrator.start()
        fig = plt.figure(figsize=(6, 4))
        axes = fig.subfigures(1, 1).add_subplot()
        fig.subplots_adjust(left=0.25, right=0.75, bottom=0.3, top=0.7)
        axes.plot([0, 1], [0, 1])
        axes.set_xlabel("an x label")
        axes.set_ylabel("a y label")
        axes.xaxis.set_label_position(xside)
        axes.yaxis.set_label_position(yside)
        fig.canvas.draw()
        QtGuiDrag.pyl_show(hide_window=True)
        fig.canvas.draw()
        self.fig = fig
        return fig, axes

    @staticmethod
    def _corner(artist):
        box = artist.get_window_extent()
        return np.array([box.x0, box.y0])

    def test_writing_a_label_back_where_it_is_leaves_it_there(self):
        for xside, yside in (("bottom", "left"), ("top", "right")):
            fig, axes = self._figure(xside, yside)
            for label, pad in (
                (axes.xaxis.label, "xaxis"),
                (axes.yaxis.label, "yaxis"),
            ):
                with self.subTest(label=pad, side=(xside, yside)):
                    before, before_pad = self._corner(label), getattr(axes, pad).labelpad
                    for _ in range(3):
                        wrapper = TargetWrapper(label)
                        wrapper.set_positions(np.array(wrapper.get_positions()))
                    fig.canvas.draw()
                    np.testing.assert_allclose(self._corner(label), before, atol=1e-6)
                    self.assertAlmostEqual(
                        getattr(axes, pad).labelpad, before_pad, places=6
                    )
            plt.close(fig)

    def test_dragging_a_label_moves_it_by_the_drag(self):
        for xside, yside in (("bottom", "left"), ("top", "right")):
            fig, axes = self._figure(xside, yside)
            for label, offset in (
                (axes.xaxis.label, (0, -15)),
                (axes.yaxis.label, (-15, 0)),
            ):
                with self.subTest(offset=offset, side=(xside, yside)):
                    before = self._corner(label)
                    self.move_element(offset, label)
                    fig.canvas.draw()
                    np.testing.assert_allclose(
                        self._corner(label) - before,
                        np.array(offset, dtype=float),
                        atol=1e-6,
                    )
                    fig.selection.clear_targets()
                    fig.figure_dragger.selected_element = None
            plt.close(fig)


if __name__ == "__main__":
    unittest.main()
