import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5 import QtCore, QtGui, QtWidgets
else:
    from qtpy import QtCore, QtGui, QtWidgets


class InfoDialog(QtWidgets.QWidget):
    def __init__(self, parent):
        """A dialog displaying the version number of pylustrator.

        Args:
            parent: the parent widget
        """
        QtWidgets.QWidget.__init__(self)
        self.setWindowTitle("Pylustrator - Info")
        self.setWindowIcon(
            QtGui.QIcon(
                os.path.join(os.path.dirname(__file__), "..", "icons", "logo.ico")
            )
        )
        self.layout = QtWidgets.QVBoxLayout(self)  # type: ignore[assignment]

        self.label = QtWidgets.QLabel("")

        pixmap = QtGui.QPixmap(
            os.path.join(os.path.dirname(__file__), "..", "icons", "logo.png")
        )
        self.label.setPixmap(pixmap)
        self.label.setMask(pixmap.mask())
        self.layout.addWidget(self.label)

        import pylustrator

        self.label = QtWidgets.QLabel("<b>Version " + pylustrator.__version__ + "</b>")
        font = self.label.font()
        font.setPointSize(16)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.layout.addWidget(self.label)

        self.label = QtWidgets.QLabel("Copyright © 2016-2022, Richard Gerum")
        self.label.setAlignment(QtCore.Qt.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.layout.addWidget(self.label)

        self.label = QtWidgets.QLabel(
            "<a href=https://pylustrator.readthedocs.io>Documentation</a>"
        )
        self.label.setAlignment(QtCore.Qt.AlignCenter)  # ty:ignore[unresolved-attribute]
        self.label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)  # ty:ignore[unresolved-attribute]
        self.label.setOpenExternalLinks(True)
        self.layout.addWidget(self.label)
