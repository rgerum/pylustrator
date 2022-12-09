from matplotlib.backend_bases import KeyEvent
from base_test_class import BaseTest
from matplotlib.legend import Legend


class TestLegend(BaseTest):

    def test_legend_properties(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[2])
        fig.window.input_properties.button_legend.clicked.emit()

        get_legend = lambda: fig.axes[2].get_legend()
        line_command = "plt.figure(1).axes[2].legend("
        test_run = "Change legend in axes."
        x = 0.040748
        y = 0.854

        self.move_element((0, 0), get_legend)

        #self.check_text_properties(get_text, line_command, test_run, 0.4931, 0.4979)
        self.change_property("loc", (x, 0.856602), lambda _: self.move_element((-1, 0)), get_legend, line_command,
                             test_run, get_function=lambda: get_legend()._loc)
        self.change_property("loc", (0.047605, 0.856602), lambda _: self.move_element((1, 0)), get_legend, line_command,
                             test_run, get_function=lambda: get_legend()._loc)
        self.change_property("loc", (0.047605, y), lambda _: self.move_element((0, -1)), get_legend, line_command,
                             test_run, get_function=lambda: get_legend()._loc)
        self.change_property("loc", (0.047605, 0.856602), lambda _: self.move_element((0, 1)), get_legend, line_command,
                             test_run, get_function=lambda: get_legend()._loc)
        #self.change_property("loc", (0.2, 0.5),
        #                     lambda _: fig.window.input_size.input_position.valueChangedX.emit(0.2), get_text,
        #                     line_command, test_run, get_function=lambda: get_text()._loc)
        #self.change_property("loc", (0.2, 0.2),
        #                     lambda _: fig.window.input_size.input_position.valueChangedY.emit(0.2), get_text,
        #                     line_command, test_run, get_function=lambda: get_text()._loc)

        self.change_property("frameon", False,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "frameon"].setChecked(False, signal=True),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().get_frame_on())

        self.change_property("borderpad", 0.2,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "borderpad"].setValue(0.2),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().borderpad)

        self.change_property("labelspacing", 1.3,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "labelspacing"].setValue(1.3),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().labelspacing)

        self.change_property("markerscale", 3,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "markerscale"].setValue(3),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().markerscale)

        self.change_property("handlelength", 3,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "handlelength"].setValue(3),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().handlelength)

        self.change_property("handletextpad", 2,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "handletextpad"].setValue(2),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().handletextpad)

        self.change_property("ncols", 2,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "ncols"].setValue(2),
                             get_legend, line_command, test_run, get_function=lambda: get_legend()._ncols)

        self.change_property("columnspacing", 2.3,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "columnspacing"].setValue(2.3),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().columnspacing)

        self.change_property("columnspacing", 2.3,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "columnspacing"].setValue(2.3),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().columnspacing)

        self.change_property("fontsize", 15,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "fontsize"].setValue(15),
                             get_legend, line_command, test_run, get_function=lambda: get_legend()._fontsize)

        self.change_property("title", "new",
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "title"].setText("new", signal=True),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().get_title().get_text())

        self.change_property("title_fontsize", 23,
                             lambda _: fig.window.input_properties.input_legend_properties.widgets[
                                 "title_fontsize"].setValue(23),
                             get_legend, line_command, test_run, get_function=lambda: get_legend().get_title().get_fontsize())


