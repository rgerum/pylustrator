import numpy as np
from base_test_class import BaseTest


class TestAxes(BaseTest):

    def test_move_axes(self):
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

