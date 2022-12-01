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

    def test_axis_limits(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_axes = lambda: fig.axes[0]
        line_command = "plt.figure(1).axes[0].set_xlim("
        test_run = "Change axes limits."

        self.move_element((0, 0), fig.axes[0])

        self.change_property("xlim", (0, 10), lambda _: self.fig.window.input_properties.input_xaxis.input_lim.setValue((0, 10), signal=True), get_axes, line_command,
                             test_run, get_function=lambda: get_axes().get_xlim())

        line_command = "plt.figure(1).axes[0].set_ylim("
        self.change_property("ylim", (-5, 8), lambda _: self.fig.window.input_properties.input_yaxis.input_lim.setValue((-5, 8), signal=True), get_axes, line_command,
                             test_run, get_function=lambda: get_axes().get_ylim())

        line_command = "plt.figure(1).axes[0].get_xaxis().get_label().set("
        self.change_property("xlabel", "label",
                             lambda _: self.fig.window.input_properties.input_xaxis.input_label.setText("label",
                                                                                                       signal=True),
                             get_axes, line_command,
                             test_run, get_function=lambda: get_axes().get_xlabel())

        line_command = "plt.figure(1).axes[0].get_yaxis().get_label().set("
        self.change_property("ylabel", "label",
                             lambda _: self.fig.window.input_properties.input_yaxis.input_label.setText("label",
                                                                                                        signal=True),
                             get_axes, line_command,
                             test_run, get_function=lambda: get_axes().get_ylabel())