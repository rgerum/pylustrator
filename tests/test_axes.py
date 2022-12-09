import numpy as np
from base_test_class import BaseTest, NotInSave


class TestAxes(BaseTest):

    def test_move_axes(self):
        # get the figure
        fig, text = self.run_plot_script()

        # and select and move the axes
        self.move_element((-1, 0), fig.axes[0])
        fig.change_tracker.save()

        # find the saved string and check the numbers
        line, (args, kwargs) = self.check_line_in_file("plt.figure(1).axes[0].set(")
        np.testing.assert_almost_equal(kwargs["position"], [0.123438, 0.11, 0.227941, 0.77], 2,
                                       "Figure movement not correctly written to file")

        # run the file again
        fig, text = self.run_plot_script()

        # test if the axes is at the right position
        np.testing.assert_almost_equal(np.array(fig.axes[0].get_position()), [[0.123438, 0.11], [0.351379, 0.88]], 2,
                                       "Saved axes not loaded correctly")

        # don't move it and save the result
        self.move_element((0, 0), fig.axes[0])
        fig.change_tracker.save()

        # the output should still be the same
        self.assertEqual(text, self.get_script_text(), "Saved differently")

    def test_axis_limits(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_axes = lambda: fig.axes[0]
        line_command = "plt.figure(1).axes[0].set("
        test_run = "Change axes limits."

        self.change_property2("xlim", (0, 10), lambda _: self.fig.window.input_properties.input_xaxis.input_lim.setValue((0, 10), signal=True), get_axes, line_command,
                             test_run)

        self.change_property2("ylim", (-5, 8), lambda _: self.fig.window.input_properties.input_yaxis.input_lim.setValue((-5, 8), signal=True), get_axes, line_command,
                             test_run)

        self.change_property2("xlabel", "label",
                             lambda _: self.fig.window.input_properties.input_xaxis.input_label.setText("label",
                                                                                                       signal=True),
                             get_axes, line_command,
                             test_run)

        self.change_property2("ylabel", "label",
                             lambda _: self.fig.window.input_properties.input_yaxis.input_label.setText("label",
                                                                                                        signal=True),
                             get_axes, line_command,
                             test_run)

        get_axes = [lambda: fig.axes[0], lambda: fig.axes[1]]
        line_command = ["plt.figure(1).axes[0].set(", "plt.figure(1).axes[1].set("]
        test_run = "Change axes limits of two axes."

        self.change_property2("xlim", (0.3, 10.7),
                              lambda _: self.fig.window.input_properties.input_xaxis.input_lim.setValue((0.3, 10.7),
                                                                                                        signal=True),
                              get_axes, line_command,
                              test_run)

        self.change_property2("ylim", (0.3, 10.7),
                              lambda _: self.fig.window.input_properties.input_yaxis.input_lim.setValue((0.3, 10.7),
                                                                                                        signal=True),
                              get_axes, line_command,
                              test_run)

        self.change_property2("xlabel", "label2",
                              lambda _: self.fig.window.input_properties.input_xaxis.input_label.setText("label2",
                                                                                                         signal=True),
                              get_axes, line_command,
                              test_run)

        self.change_property2("ylabel", "label2",
                              lambda _: self.fig.window.input_properties.input_yaxis.input_label.setText("label2",
                                                                                                         signal=True),
                              get_axes, line_command,
                              test_run)
    def test_axis_grid(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_axes = lambda: fig.axes[0]
        line_command = "plt.figure(1).axes[0].grid("
        test_run = "Change axes grid."

        self.change_property("grid", True, lambda _: self.fig.window.input_properties.button_grid.clicked.emit(True), get_axes, line_command,
                             test_run, get_function=lambda: getattr(get_axes(), "_gridOnMajor", False) or getattr(get_axes().xaxis, "_major_tick_kw", {"gridOn": False})['gridOn'])

    def test_axis_despine(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_axes = lambda: fig.axes[0]
        line_command = "plt.figure(1).axes[0].spines[['right', 'top']].set_visible("
        test_run = "Change axes despine."

        self.change_property("despine", False, lambda _: self.fig.window.input_properties.button_despine.clicked.emit(True), get_axes, line_command,
                             test_run, get_function=lambda: get_axes().spines['right'].get_visible() and get_axes().spines['top'].get_visible())

    def test_axis_ticks(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_axes = lambda: fig.axes[0]
        test_run = "Change axes ticks."
        line_command = "plt.figure(1).axes[0].set("

        def check_saved_property(xy):
            def check():
                # find the saved string and check the numbers
                line, (args, kwargs) = self.check_line_in_file(line_command)
                self.assertEqualStringOrArray([1., 2.2, 3., 5.], kwargs[f"{xy}ticks"],
                                              f"Property 'ticks' not saved correctly. [{test_run}]")
                self.assertEqualStringOrArray(["1", "2.2", "3", "5"], kwargs[f"{xy}ticklabels"],
                                              f"Property 'ticks' not saved correctly. [{test_run}]")
            return check

        # test_saved_value
        def set_ticks(_):
            self.fig.window.input_properties.input_xaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_xaxis.tick_edit.input_ticks.setText("1\n2.2\n3\n5", signal=True)

        self.change_property("xticks", [1., 2.2, 3., 5.], set_ticks, get_axes, line_command, test_run, test_saved_value=check_saved_property("x"))

        def set_ticks(_):
            self.fig.window.input_properties.input_yaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_yaxis.tick_edit.input_ticks.setText("1\n2.2\n3\n5", signal=True)

        self.change_property("yticks", [1., 2.2, 3., 5.], set_ticks, get_axes, line_command, test_run, test_saved_value=check_saved_property("y"))

        def check_saved_property(xy):
            def check():
                # find the saved string and check the numbers
                line, (args, kwargs) = self.check_line_in_file(line_command)
                self.assertEqualStringOrArray([1., 2., 3., 5., 10], kwargs[f"{xy}ticks"],
                                              f"Property 'ticks' not saved correctly. [{test_run}]")
                self.assertEqualStringOrArray(["a", "b", "c", "5", r'$\mathdefault{10^{1}}$'], kwargs[f"{xy}ticklabels"],
                                              f"Property 'ticks' not saved correctly. [{test_run}]")

        # test_saved_value
        def set_ticks(_):
            self.fig.window.input_properties.input_xaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_xaxis.tick_edit.input_ticks.setText('1 "a"\n2 "b\n3 c\n5\n10^1', signal=True)

        self.change_property("xticks", [1., 2., 3., 5., 10], set_ticks, get_axes, line_command, test_run,
                             test_saved_value=check_saved_property("x"))

        def set_ticks(_):
            self.fig.window.input_properties.input_yaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_yaxis.tick_edit.input_ticks.setText('1 "a"\n2 "b\n3 c\n5\n10^1', signal=True)

        self.change_property("yticks", [1., 2., 3., 5., 10], set_ticks, get_axes, line_command, test_run,
                             test_saved_value=check_saved_property("y"))

        def set_xlog(_):
            self.fig.window.input_properties.input_xaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_xaxis.tick_edit.input_scale.setText("log", signal=True)

        self.change_property("xscale", "log", set_xlog, get_axes, line_command, test_run)

        def set_ylog(_):
            self.fig.window.input_properties.input_yaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_yaxis.tick_edit.input_scale.setText("log", signal=True)

        self.change_property("yscale", "log", set_ylog, get_axes, line_command, test_run)

    def test_minor_axis_ticks(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_axes = lambda: fig.axes[0]
        test_run = "Change axes ticks."

        self.move_element((0, 0), fig.axes[0])

        line_command = "plt.figure(1).axes[0].set_xticks("

        def check_saved_property(xy):
            def check():
                # find the saved string and check the numbers
                line, (args, kwargs) = self.check_line_in_file(line_command)
                self.assertEqualStringOrArray(True, kwargs["minor"], f"Property 'ticks' not saved correctly. [{test_run}]")
                self.assertEqualStringOrArray([0.01, 0.1, 0.2, 0.3, 0.5], args[0],
                                              f"Property 'ticks' not saved correctly. [{test_run}]")
                self.assertEqualStringOrArray([r'$\mathdefault{10^{-2}}$', "a", "b", "c", "0.5"],
                                              args[1],
                                              f"Property 'ticks' not saved correctly. [{test_run}]")

            return check
        # minor ticks
        def set_ticks(_):
            self.fig.window.input_properties.input_xaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_xaxis.tick_edit.input_ticks2.setText('10^-2\n0.1 "a"\n0.2 "b\n0.3 c\n0.5',
                                                                                       signal=True)

        self.change_property2("xticks", [0.01, 0.1, 0.2, 0.3, 0.5], set_ticks, get_axes, line_command, test_run,
                             test_saved_value=check_saved_property("x"), get_function=lambda: get_axes().get_xticks(minor=True))

        def set_ticks(_):
            self.fig.window.input_properties.input_yaxis.tick_edit.setTarget(get_axes())
            self.fig.window.input_properties.input_yaxis.tick_edit.input_ticks2.setText('10^-2\n0.1 "a"\n0.2 "b\n0.3 c\n0.5',
                                                                                       signal=True)

        self.change_property2("yticks", [0.01, 0.1, 0.2, 0.3, 0.5], set_ticks, get_axes, line_command, test_run,
                             test_saved_value=check_saved_property("y"), get_function=lambda: get_axes().get_yticks(minor=True))

    def test_axes_alignment(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = [lambda: fig.axes[0], lambda: fig.axes[1]]
        line_command = ["plt.figure(1).axes[0].set(", "plt.figure(1).axes[1].set("]
        test_run = "Align axes."

        # align left
        fig.axes[0].set_position([0.2, 0.2, 0.4, 0.4])
        fig.axes[1].set_position([0.6, 0.1, 0.3, 0.3])
        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])

        self.change_property2("position", [([0.2, 0.2], [0.6, 0.6]), ([0.2, 0.1], [0.5, 0.4])],
                              lambda _: fig.window.input_align.buttons[0].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[NotInSave, (0.2, 0.1, 0.3, 0.3)])

        # align center
        fig.axes[0].set_position([0.2, 0.2, 0.4, 0.4])
        fig.axes[1].set_position([0.6, 0.1, 0.3, 0.3])
        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])

        self.change_property2("position", [([0.35, 0.2], [0.75, 0.6]), ([0.4, 0.1], [0.7, 0.4])],
                              lambda _: fig.window.input_align.buttons[1].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.35, 0.2, 0.4, 0.4], [0.4, 0.1, 0.3, 0.3]])

        # align right
        fig.axes[0].set_position([0.2, 0.2, 0.4, 0.4])
        fig.axes[1].set_position([0.6, 0.1, 0.3, 0.3])
        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])

        self.change_property2("position", [[[0.5, 0.2], [0.9, 0.6]], [[0.6, 0.1], [0.9, 0.4]]],
                              lambda _: fig.window.input_align.buttons[2].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.5, 0.2, 0.4, 0.4], [0.6, 0.1, 0.3, 0.3]])

        # align top
        fig.axes[0].set_position([0.2, 0.2, 0.4, 0.4])
        fig.axes[1].set_position([0.6, 0.1, 0.3, 0.3])
        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])

        self.change_property2("position", [[[0.2, 0.2], [0.6, 0.6]], [[0.6, 0.3], [0.9, 0.6]]],
                              lambda _: fig.window.input_align.buttons[4].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.2, 0.2, 0.4, 0.4], [0.6, 0.3, 0.3, 0.3]])

        # align center
        fig.axes[0].set_position([0.2, 0.2, 0.4, 0.4])
        fig.axes[1].set_position([0.6, 0.1, 0.3, 0.3])
        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])

        self.change_property2("position", [[[0.2, 0.15], [0.6, 0.55]], [[0.6, 0.2], [0.9, 0.5]]],
                              lambda _: fig.window.input_align.buttons[5].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.2, 0.15, 0.4, 0.4], [0.6, 0.2, 0.3, 0.3]])

        # align bottom
        fig.axes[0].set_position([0.2, 0.2, 0.4, 0.4])
        fig.axes[1].set_position([0.6, 0.1, 0.3, 0.3])
        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])

        self.change_property2("position", [[[0.2, 0.1], [0.6, 0.5]], [[0.6, 0.1], [0.9, 0.4]]],
                              lambda _: fig.window.input_align.buttons[6].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.2, 0.1, 0.4, 0.4], [0.6, 0.1, 0.3, 0.3]])

    def test_axes_distribute(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = [lambda: fig.axes[0], lambda: fig.axes[1], lambda: fig.axes[2]]
        line_command = ["plt.figure(1).axes[0].set(", "plt.figure(1).axes[1].set(", "plt.figure(1).axes[2].set("]
        test_run = "Distribute axes."

        # distribute X
        fig.axes[0].set_position([0.2, 0.2, 0.3, 0.3])
        fig.axes[1].set_position([0.6, 0.6, 0.2, 0.2])
        fig.axes[2].set_position([0.5, 0.5, 0.4, 0.4])

        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])
        fig.change_tracker.addNewAxesChange(fig.axes[2])

        self.change_property2("position", [[[0.2, 0.2], [0.5, 0.5]],
                                           [[0.7, 0.6], [0.9, 0.8]],
                                           [[0.4, 0.5], [0.8, 0.9]]],
                              lambda _: fig.window.input_align.buttons[3].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.2, 0.2, 0.3, 0.3], [0.7, 0.6, 0.2, 0.2], [0.4, 0.5, 0.4, 0.4]])

        # distribute Y
        fig.axes[0].set_position([0.2, 0.2, 0.3, 0.3])
        fig.axes[1].set_position([0.6, 0.6, 0.2, 0.2])
        fig.axes[2].set_position([0.5, 0.5, 0.4, 0.4])

        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])
        fig.change_tracker.addNewAxesChange(fig.axes[2])

        self.change_property2("position", [[[0.2, 0.2], [0.5, 0.5]],
                                           [[0.6, 0.7], [0.8, 0.9]],
                                           [[0.5, 0.4], [0.9, 0.8]]],
                              lambda _: fig.window.input_align.buttons[7].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.2, 0.2, 0.3, 0.3], [0.6, 0.7, 0.2, 0.2], [0.5, 0.4, 0.4, 0.4]])

    def test_axes_grid(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = [lambda: fig.axes[0], lambda: fig.axes[1], lambda: fig.axes[2]]
        line_command = ["plt.figure(1).axes[0].set(", "plt.figure(1).axes[1].set(", "plt.figure(1).axes[2].set("]
        test_run = "Distribute axes."

        # distribute X
        fig.axes[0].set_position([0.2, 0.2, 0.3, 0.3])
        fig.axes[1].set_position([0.2, 0.6, 0.2, 0.2])
        fig.axes[2].set_position([0.5, 0.21, 0.25, 0.25])

        fig.change_tracker.addNewAxesChange(fig.axes[0])
        fig.change_tracker.addNewAxesChange(fig.axes[1])
        fig.change_tracker.addNewAxesChange(fig.axes[2])

        self.change_property2("position", [[[0.2, 0.2], [0.45, 0.45]],
                                           [[0.2, 0.55], [0.45, 0.8]],
                                           [[0.5, 0.2], [0.75, 0.45]]],
                              lambda _: fig.window.input_align.buttons[8].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[[0.2, 0.2, 0.25, 0.25],
                                                     [0.2, 0.55, 0.25, 0.25],
                                                     [0.5, 0.2, 0.25, 0.25]])
