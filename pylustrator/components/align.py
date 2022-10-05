import os
from qtpy import QtGui, QtWidgets


class Align(QtWidgets.QWidget):
    def __init__(self, layout: QtWidgets.QLayout, signals: "Signals"):
        """ A widget that allows to align the elements of a multi selection.

        Args:
            layout: the layout to which to add the widget
            fig: the target figure
        """
        QtWidgets.QWidget.__init__(self)
        layout.addWidget(self)

        signals.figure_changed.connect(self.setFigure)

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        actions = ["left_x", "center_x", "right_x", "distribute_x", "top_y", "center_y", "bottom_y", "distribute_y", "group"]
        icons = ["left_x.png", "center_x.png", "right_x.png", "distribute_x.png", "top_y.png", "center_y.png",
                 "bottom_y.png", "distribute_y.png", "group.png"]
        self.buttons = []
        align_group = QtWidgets.QButtonGroup(self)
        for index, act in enumerate(actions):
            button = QtWidgets.QPushButton(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "icons", icons[index])),
                                           "")
            button.setToolTip(act.replace('_', ' '))
            self.layout.addWidget(button)
            button.clicked.connect(lambda x, act=act: self.execute_action(act))
            self.buttons.append(button)
            align_group.addButton(button)
            if index == 3 or index == 7:
                line = QtWidgets.QFrame()
                line.setFrameShape(QtWidgets.QFrame.VLine)
                line.setFrameShadow(QtWidgets.QFrame.Sunken)
                self.layout.addWidget(line)
        self.layout.addStretch()

    def execute_action(self, act: str):
        """ execute an alignment action """
        self.fig.selection.align_points(act)
        self.fig.selection.update_selection_rectangles()
        self.fig.canvas.draw()

    def setFigure(self, fig):
        self.fig = fig