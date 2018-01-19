from qtpy import QtCore, QtGui, QtWidgets
import numpy as np
import matplotlib as mpl
""" Color Chooser """

def AddQColorChoose(layout, text, value=None, strech=False):
    # add a layout
    horizontal_layout = QtWidgets.QHBoxLayout()
    layout.addLayout(horizontal_layout)
    # add a text
    # text = QtWidgets.QLabel(text)
    button = QtWidgets.QPushButton("")

    # button.label = text

    def OpenDialog():
        # get new color from color picker
        qcolor = QtGui.QColor(*np.array(mpl.colors.to_rgb(button.getColor())) * 255)
        color = QtWidgets.QColorDialog.getColor(qcolor)
        # if a color is set, apply it
        if color.isValid():
            color = "#%02x%02x%02x" % color.getRgb()[:3]
            button.setColor(color)
            lineEdit.setText(color)
            try:
                button.color_changed(color)
            except AttributeError:
                pass

    def setColor(value):
        # display and save the new color
        button.setStyleSheet("background-color: %s;" % value)
        button.color = value
        try:
            button.color_changed(value)
        except AttributeError:
            pass

    def getColor():
        # return the color
        return button.color

    def editFinished():
        new_color = lineEdit.text()
        setColor(new_color)

    # default value for the color
    if value is None:
        value = "#FF0000"

    lineEdit = QtWidgets.QLineEdit()
    lineEdit.setFixedWidth(50)
    lineEdit.setText(value)
    # lineEdit.label = text
    lineEdit.editingFinished.connect(editFinished)

    # add functions to button
    button.pressed.connect(OpenDialog)
    button.setColor = setColor
    button.getColor = getColor
    # set the color
    button.setColor(value)
    # add widgets to the layout
    # horizontal_layout.addWidget(text)
    horizontal_layout.addWidget(button)
    horizontal_layout.addWidget(lineEdit)
    # add a strech if requested
    if strech:
        horizontal_layout.addStretch()
    return button