from matplotlib.backend_bases import KeyEvent
from base_test_class import BaseTest
from matplotlib.legend import Legend


class TestLegend(BaseTest):

    def test_legend_properties(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[2])
        fig.window.input_properties.button_legend.clicked.emit()

        get_text = lambda: fig.axes[2].get_legend()
        line_command = "plt.figure(1).axes[2].legend("
        test_run = "Change existing text in axes."
        x = 0.041
        y = 0.854

        #self.change_property("borderpad", 0.2,
        #                     lambda _: fig.window.input_properties.input_legend_properties.widgets["borderpad"].setValue(0.2),
        #                     get_text, line_command, test_run, get_function=lambda: get_text().borderpad)

        #self.check_text_properties(get_text, line_command, test_run, 0.4931, 0.4979)
        self.change_property("loc", (x, 0.857), lambda _: self.move_element((-1, 0)), get_text, line_command,
                             test_run, get_function=lambda: get_text()._loc)
        self.change_property("loc", (0.048, 0.857), lambda _: self.move_element((1, 0)), get_text, line_command,
                             test_run, get_function=lambda: get_text()._loc)
        self.change_property("loc", (0.048, y), lambda _: self.move_element((0, -1)), get_text, line_command,
                             test_run, get_function=lambda: get_text()._loc)
        self.change_property("loc", (0.048, 0.857), lambda _: self.move_element((0, 1)), get_text, line_command,
                             test_run, get_function=lambda: get_text()._loc)
        #self.change_property("loc", (0.2, 0.5),
        #                     lambda _: fig.window.input_size.input_position.valueChangedX.emit(0.2), get_text,
        #                     line_command, test_run, get_function=lambda: get_text()._loc)
        #self.change_property("loc", (0.2, 0.2),
        #                     lambda _: fig.window.input_size.input_position.valueChangedY.emit(0.2), get_text,
        #                     line_command, test_run, get_function=lambda: get_text()._loc)


