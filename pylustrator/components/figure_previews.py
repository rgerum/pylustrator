from qtpy import QtCore, QtWidgets, QtGui


class FigurePreviews(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()
        self.figures = []
        self.buttons = []
        self.parent = parent

        layout = QtWidgets.QVBoxLayout(self)
        self.layout2 = QtWidgets.QVBoxLayout()
        layout.addLayout(self.layout2)
        layout.addStretch()

    def addFigure(self, figure):
        self.figures.append(figure)
        button = QtWidgets.QLabel("figure")
        self.buttons.append(button)
        self.layout2.addWidget(button)

        button.setAlignment(QtCore.Qt.AlignCenter)
        pix = QtGui.QPixmap(20, 30)
        pix.fill(QtGui.QColor("#666666"))

        target_width = 150
        target_height = 150*9/16
        w, h = figure.get_size_inches()
        figure.savefig("tmp.png", dpi=min([target_width/w, target_height/h]))
        button.setStyleSheet("background:#d1d1d1")
        button.setMaximumWidth(150)
        button.setMaximumHeight(150)
        self.setMaximumWidth(150)

        pix.load("tmp.png")
        # scale pixmap to fit in label'size and keep ratio of pixmap
        #pix = pix.scaled(160, 90, QtCore.Qt.KeepAspectRatio)
        button.setPixmap(pix)
        button.mousePressEvent = lambda e: self.parent.setFigure(figure)
