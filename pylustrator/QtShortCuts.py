from qtpy import QtCore, QtGui, QtWidgets
import numpy as np
import matplotlib as mpl


def getColorFromCoordinates(p):
    desktop = QtWidgets.QApplication.desktop()
    pixmap = QtWidgets.QGuiApplication.screens().at(desktop.screenNumber()).grabWindow(desktop.winId(),
                                                                                         p.x(), p.y(), 1, 1)
    i = pixmap.toImage()
    return i.pixel(0, 0)


""" Color Chooser """

class QDragableColor(QtWidgets.QLineEdit):
    color_changed = QtCore.Signal(str)

    def __init__(self, value):
        QtWidgets.QLineEdit.__init__(self, value)
        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignHCenter)
        self.setColor(value, True)

    def setColor(self, value, no_signal=False):
        # display and save the new color
        self.setStyleSheet("text-align: center; background-color: %s; border: 2px solid black" % value)
        self.color = value
        self.setText(value)
        self.color_changed.emit(value)

    def getColor(self):
        # return the color
        return self.color

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            drag = QtGui.QDrag(self)
            drag.setPixmap(self.grab())
            mime = QtCore.QMimeData()
            mime.setText(self.color)
            drag.setMimeData(mime)
            self.setStyleSheet("background-color: lightgray; border: 2px solid gray")
            self.setDisabled(True)
            self.setText("")
            drag.exec()
            self.setText(self.color)
            self.setDisabled(False)
            self.setStyleSheet("text-align: center; background-color: %s; border: 2px solid black" % self.color)
        elif event.button() == QtCore.Qt.RightButton:
            self.openDialog()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("text/plain") and event.source() != self:
            event.acceptProposedAction()
            self.setStyleSheet("background-color: %s; border: 2px solid red" % self.color)

    def dragLeaveEvent(self, event):
        self.setStyleSheet("background-color: %s; border: 2px solid black" % self.color)

    def dropEvent(self, event):
        color = event.source().getColor()
        event.source().setColor(self.getColor())
        self.setColor(color)

    def openDialog(self):
        # get new color from color picker
        qcolor = QtGui.QColor(*np.array(mpl.colors.to_rgb(self.getColor())) * 255)
        color = QtWidgets.QColorDialog.getColor(qcolor)
        # if a color is set, apply it
        if color.isValid():
            color = "#%02x%02x%02x" % color.getRgb()[:3]
            self.setColor(color)


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