from matplotlib.backend_bases import KeyEvent
from base_test_class import BaseTest, NotInSave


class TestText(BaseTest):

    def test_text_properties_axes_existing(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = lambda: fig.axes[0].texts[0]
        line_command = "plt.figure(1).axes[0].texts[0].set("
        test_run = "Change existing text in axes."
        self.check_text_properties(get_text, line_command, test_run, 0.4931, 0.497294)

    def test_text_properties_axes_new(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.axes[0].texts[-1]
        line_command = "plt.figure(1).axes[0].text("
        test_run = "Change new text in axes."

        self.check_text_properties(get_text, line_command, test_run, 0.4931, 0.497294)

    def test_text_properties_figure_existing(self):
        # get the figure
        fig, text = self.run_plot_script()

        get_text = lambda: fig.texts[-1]
        line_command = "plt.figure(1).texts[0].set("
        test_run = "Change existing text in Figure."

        self.check_text_properties(get_text, line_command, test_run, 0.4984, 0.4979)

    def test_text_properties_figure_new(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig)
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.texts[-1]
        line_command = "plt.figure(1).text("
        test_run = "Change new text in Figure."

        self.check_text_properties(get_text, line_command, test_run, 0.4984, 0.4979)

    def test_text_property_together(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = [lambda: fig.axes[0].texts[0], lambda: fig.axes[0].texts[-1]]
        line_command = ["plt.figure(1).axes[0].texts[0].set(", "plt.figure(1).axes[0].text("]
        test_run = "Change two texts together in axes."

        self.check_text_properties(get_text, line_command, test_run, 0.493, 0.497)

    def test_text_alignment(self):
        # get the figure
        fig, text = self.run_plot_script()

        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = [lambda: fig.axes[0].texts[0], lambda: fig.axes[0].texts[1]]
        line_command = ["plt.figure(1).axes[0].texts[0].set(", "plt.figure(1).axes[0].text("]
        test_run = "Align texts in axes."

        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        # align left
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        self.change_property2("position", [(0.2, 0.2), (0.2, 0.6)],
                              lambda _: fig.window.input_align.buttons[0].clicked.emit(0), get_text, line_command,
                              test_run, value2_list=[NotInSave, (0.2, 0.6)])

        # align center
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        self.change_property2("position", [(0.55, 0.2), (0.472, 0.6)],
                              lambda _: fig.window.input_align.buttons[1].clicked.emit(0), get_text, line_command,
                              test_run)

        # align right
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        self.change_property2("position", [(0.834, 0.2), (0.6, 0.6)],
                              lambda _: fig.window.input_align.buttons[2].clicked.emit(0), get_text, line_command,
                              test_run)

        # align top
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        self.change_property2("position", [(0.2, 0.6), (0.6, 0.6)],
                              lambda _: fig.window.input_align.buttons[4].clicked.emit(0), get_text, line_command,
                              test_run)

        # align center
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        self.change_property2("position", [(0.2, 0.404), (0.6, 0.404)],
                              lambda _: fig.window.input_align.buttons[5].clicked.emit(0), get_text, line_command,
                              test_run)

        # align bottom
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])

        self.change_property2("position", [(0.2, 0.2), (0.6, 0.2)],
                              lambda _: fig.window.input_align.buttons[6].clicked.emit(0), get_text, line_command,
                              test_run)

    def test_text_distribute(self):
        # get the figure
        fig, text = self.run_plot_script()

        # create two additional text so that we have 3 in total
        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()
        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = [lambda: fig.axes[0].texts[0], lambda: fig.axes[0].texts[1]]
        line_command = ["plt.figure(1).axes[0].texts[0].set(", "plt.figure(1).axes[0].text(", "plt.figure(1).axes[0].text("]
        test_run = "Distribute texts in axes."

        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[2])

        # distribute X
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.axes[0].texts[2].set_position([0.5, 0.5])

        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[2])

        self.change_property2("position", [(0.2, 0.2), (1.0301, 0.6), (0.5, 0.5)],
                              lambda _: fig.window.input_align.buttons[3].clicked.emit(0), get_text, line_command,
                              test_run)

        # distribute Y
        fig.axes[0].texts[0].set_position([0.2, 0.2])
        fig.axes[0].texts[1].set_position([0.6, 0.6])
        fig.axes[0].texts[2].set_position([0.5, 0.5])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[0])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[1])
        fig.change_tracker.addNewTextChange(fig.axes[0].texts[2])

        self.change_property2("position", [(0.2, 0.2), (0.6, 0.6460), (0.5, 0.5)],
                              lambda _: fig.window.input_align.buttons[7].clicked.emit(0), get_text, line_command,
                              test_run)

    def test_text_delete(self):
        # get the figure
        fig, text = self.run_plot_script()

        # create two additional text so that we have 3 in total
        fig.figure_dragger.select_element(fig.axes[0])
        fig.window.input_properties.button_add_text.clicked.emit()

        get_text = lambda: fig.axes[0].texts[0]
        line_command = "plt.figure(1).axes[0].texts[0].set("
        test_run = "Delete text in axes."

        self.change_property2("visible", False,
                              lambda _: fig.figure_dragger.selection.keyPressEvent(KeyEvent('delete', fig.canvas, "delete")), get_text, line_command,
                              test_run)

        get_text = lambda: fig.axes[0].texts[1]
        line_command = "plt.figure(1).axes[0].text("
        test_run = "Delete new text in axes."

        self.change_property2("visible", False,
                             lambda _: fig.figure_dragger.selection.keyPressEvent(
                                 KeyEvent('delete', fig.canvas, "delete")), get_text, line_command,
                             test_run, delete=True)

    def check_text_properties(self, get_text, line_command, test_run, x, y):
        fig = self.fig
        self.change_property2("position", (x, 0.5), lambda _: self.move_element((-1, 0)), get_text, line_command, test_run)
        self.move_element((1, 0), get_text)
        self.change_property2("position", (0.5, y), lambda _: self.move_element((0, -1)), get_text, line_command, test_run)
        self.move_element((0, 1), get_text)
        self.change_property2("position", (0.2, 0.5), lambda _: fig.window.input_size.input_position.valueChangedX.emit(0.2), get_text, line_command, test_run)
        self.change_property2("position", (0.2, 0.2), lambda _: fig.window.input_size.input_position.valueChangedY.emit(0.2), get_text, line_command, test_run)
        self.change_property2("weight", "bold", lambda _: fig.window.input_properties.input_font_properties.button_bold.clicked.emit(True), get_text, line_command, test_run)
        self.change_property2("weight", "normal", lambda _: fig.window.input_properties.input_font_properties.button_bold.clicked.emit(False), get_text, line_command, test_run, value2_list=None)
        self.change_property2("style", "italic", lambda _: fig.window.input_properties.input_font_properties.button_italic.clicked.emit(True), get_text, line_command, test_run)
        self.change_property2("style", "normal", lambda _: fig.window.input_properties.input_font_properties.button_italic.clicked.emit(False), get_text, line_command, test_run, value2_list=None)
        self.change_property2("ha", "left", lambda _: fig.window.input_properties.input_font_properties.buttons_align[0].clicked.emit(True), get_text, line_command, test_run, value2_list=None)
        self.change_property2("ha", "center", lambda _: fig.window.input_properties.input_font_properties.buttons_align[1].clicked.emit(True), get_text, line_command, test_run)
        self.change_property2("ha", "right", lambda _: fig.window.input_properties.input_font_properties.buttons_align[2].clicked.emit(True), get_text, line_command, test_run)
        self.change_property2("color", "#FF0000", lambda _: fig.window.input_properties.input_font_properties.button_color.valueChanged.emit("#FF0000"), get_text, line_command, test_run)
        self.change_property2("fontsize", 8, lambda _: fig.window.input_properties.input_font_properties.font_size.valueChanged.emit(8), get_text, line_command, test_run)
        self.change_property2("text", "update", lambda _: fig.window.input_properties.input_text.setText("update", signal=True), get_text, line_command, test_run)
        self.change_property2("rotation", 45, lambda _: fig.window.input_properties.input_rotation.setValue(45, signal=True), get_text, line_command, test_run)
