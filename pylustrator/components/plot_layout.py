import os
import numpy as np

from qtpy import QtCore, QtGui, QtWidgets
import matplotlib.transforms as transforms
from matplotlib.figure import Figure

from qtpy import API_NAME as QT_API_NAME
if QT_API_NAME.startswith("PyQt4"):
    from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as Canvas
    from matplotlib.backends.backend_qt4 import NavigationToolbar2QT as NavigationToolbar
else:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
    from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar


from .matplotlibwidget import MatplotlibWidget


class Canvas(QtWidgets.QWidget):
    fitted_to_view = False
    footer_label = None
    footer_label2 = None

    canvas = None

    def __init__(self, signals: "Signals"):
        """ The wrapper around the matplotlib canvas to create a more image editor like canvas with background and side rulers
        """
        super().__init__()

        signals.figure_changed.connect(self.setFigure)
        signals.figure_size_changed.connect(lambda: (self.updateFigureSize(), self.updateRuler()))
        self.signals = signals

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.canvas_canvas = QtWidgets.QWidget(self)
        self.layout.addWidget(self.canvas_canvas)
        self.canvas_canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.canvas_canvas.setStyleSheet("background:#d1d1d1")
        self.canvas_canvas.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.shadow = QtWidgets.QLabel(self.canvas_canvas)
        self.canvas_border = QtWidgets.QLabel(self.canvas_canvas)

        self.canvas_container = QtWidgets.QWidget(self.canvas_canvas)
        self.canvas_wrapper_layout = QtWidgets.QHBoxLayout()
        self.canvas_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas_container.setLayout(self.canvas_wrapper_layout)

        self.canvas_container.setStyleSheet("background:blue")

        self.x_scale = QtWidgets.QLabel(self.canvas_canvas)
        self.y_scale = QtWidgets.QLabel(self.canvas_canvas)

        if 0:
            self.canvas = MatplotlibWidget(self, number, size=size, *args, **kwargs)
            self.canvas.window_pylustrator = self
            self.canvas_wrapper_layout.addWidget(self.canvas)
            self.fig = self.canvas.figure
            self.fig.widget = self.canvas

            self.fig.figure_size_changed = self.figure_size_changed
            self.figure_size_changed.connect(lambda: (self.updateFigureSize(), self.updateRuler()))

            #self.canvas_canvas.mousePressEvent = lambda event: self.canvas.mousePressEvent(event)
            #self.canvas_canvas.mouseReleaseEvent = lambda event: self.canvas.mouseReleaseEvent(event)

            self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)

            self.fig.canvas.mpl_connect('scroll_event', self.scroll_event)
            self.fig.canvas.mpl_connect('key_press_event', self.canvas_key_press)
            self.fig.canvas.mpl_connect('key_release_event', self.canvas_key_release)
            self.control_modifier = False

            self.fig.canvas.mpl_connect('button_press_event', self.button_press_event)
            self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move_event)
            self.fig.canvas.mpl_connect('button_release_event', self.button_release_event)
            self.drag = None

    def setFigure(self, figure):
        if self.canvas is not None:
            self.canvas_wrapper_layout.removeWidget(self.canvas)
            del self.canvas

        self.canvas = MatplotlibWidget(self, figure=figure)
        self.canvas.window_pylustrator = self
        self.canvas_wrapper_layout.addWidget(self.canvas)

        self.canvas_wrapper_layout.addWidget(self.canvas)
        self.fig = self.canvas.figure
        self.fig.widget = self.canvas

        self.fig.canvas.mpl_disconnect(self.fig.canvas.manager.key_press_handler_id)

        self.fig.canvas.mpl_connect('scroll_event', self.scroll_event)
        self.fig.canvas.mpl_connect('key_press_event', self.canvas_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.canvas_key_release)
        self.control_modifier = False

        self.fig.canvas.mpl_connect('button_press_event', self.button_press_event)
        self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move_event)
        self.fig.canvas.mpl_connect('button_release_event', self.button_release_event)
        self.drag = None

        self.signals.canvas_changed.emit(self.canvas)

    def setFooters(self, footer, footer2):
        self.footer_label = footer
        self.footer_label2 = footer2

    def updateRuler(self):
        """ update the ruler around the figure to show the dimensions """
        trans = transforms.Affine2D().scale(1. / 2.54, 1. / 2.54) + self.fig.dpi_scale_trans
        l = 20
        l1 = 20
        l2 = 10
        l3 = 5

        w = self.canvas_canvas.width()
        h = self.canvas_canvas.height()

        self.pixmapX = QtGui.QPixmap(w, l)
        self.pixmapY = QtGui.QPixmap(l, h)

        self.pixmapX.fill(QtGui.QColor("#f0f0f0"))
        self.pixmapY.fill(QtGui.QColor("#f0f0f0"))

        painterX = QtGui.QPainter(self.pixmapX)
        painterY = QtGui.QPainter(self.pixmapY)

        painterX.setPen(QtGui.QPen(QtGui.QColor("black"), 1))
        painterY.setPen(QtGui.QPen(QtGui.QColor("black"), 1))

        offset = self.canvas_container.pos().x()
        start_x = np.floor(trans.inverted().transform((-offset, 0))[0])
        end_x = np.ceil(trans.inverted().transform((-offset + w, 0))[0])
        dx = 0.1

        pix_per_cm = trans.transform((0, 1))[1] - trans.transform((0, 0))[1]
        big_lines = int(self.fontMetrics().height() * 5 / pix_per_cm)
        medium_lines = big_lines / 2
        dx = big_lines / 10

        positions = np.hstack([np.arange(0, start_x, -dx)[::-1], np.arange(0, end_x, dx)])
        for i, pos_cm in enumerate(positions):
        #for i, pos_cm in enumerate(np.arange(start_x, end_x, dx)):
            x = (trans.transform((pos_cm, 0))[0] + offset)
            if pos_cm % big_lines == 0:
                painterX.drawLine(int(x), int(l - l1 - 1), int(x), int(l - 1))
                text = str("%d" % np.round(pos_cm))
                o = 0
                painterX.drawText(int(x + 3), int(o - 3), int(self.fontMetrics().width(text)), int(o + self.fontMetrics().height()),
                                  QtCore.Qt.AlignLeft,
                                  text)
            elif pos_cm % medium_lines == 0:
                painterX.drawLine(int(x), int(l - l2 - 1), int(x), int(l - 1))
            else:
                painterX.drawLine(int(x), int(l - l3 - 1), int(x), int(l - 1))
        painterX.drawLine(0, l - 2, w, l - 2)
        painterX.setPen(QtGui.QPen(QtGui.QColor("white"), 1))
        painterX.drawLine(0, l - 1, w, l - 1)
        self.x_scale.setPixmap(self.pixmapX)
        self.x_scale.setMinimumSize(w, l)
        self.x_scale.setMaximumSize(w, l)

        offset = self.canvas_container.pos().y() + self.canvas_container.height()
        start_y = np.floor(trans.inverted().transform((0, +offset - h))[1])
        end_y = np.ceil(trans.inverted().transform((0, +offset))[1])
        dy = 0.1

        big_lines = 1
        medium_lines = 0.5

        pix_per_cm = trans.transform((0, 1))[1]-trans.transform((0, 0))[1]
        big_lines = int(self.fontMetrics().height()*5/pix_per_cm)
        medium_lines = big_lines / 2
        dy = big_lines / 10

        positions = np.hstack([np.arange(0, start_y, -dy)[::-1], np.arange(0, end_y, dy)])
        for i, pos_cm in enumerate(positions):
            y = (-trans.transform((0, pos_cm))[1] + offset)
            if pos_cm % big_lines == 0:
                painterY.drawLine(int(l - l1 - 1), int(y), int(l - 1), int(y))
                text = str("%d" % np.round(pos_cm))
                o = 0
                for ti, t in enumerate(text):
                    painterY.drawText(int(o), int(y + 3 + self.fontMetrics().height()*ti),
                                      int(o + self.fontMetrics().width("0")), int(self.fontMetrics().height()),
                                      QtCore.Qt.AlignCenter, t)
            elif pos_cm % medium_lines == 0:
                painterY.drawLine(int(l - l2 - 1), int(y), int(l - 1), int(y))
            else:
                painterY.drawLine(int(l - l3 - 1), int(y), int(l - 1), int(y))
        painterY.drawLine(int(l - 2), 0, int(l - 2), int(h))
        painterY.setPen(QtGui.QPen(QtGui.QColor("white"), 1))
        painterY.drawLine(int(l - 1), 0, int(l - 1), int(h))
        painterY.setPen(QtGui.QPen(QtGui.QColor("#f0f0f0"), 0))
        painterY.setBrush(QtGui.QBrush(QtGui.QColor("#f0f0f0")))
        painterY.drawRect(0, 0, int(l), int(l))
        self.y_scale.setPixmap(self.pixmapY)
        self.y_scale.setMinimumSize(l, h)
        self.y_scale.setMaximumSize(l, h)

        w, h = self.canvas.get_width_height()

        self.pixmap = QtGui.QPixmap(w, h)

        self.pixmap.fill(QtGui.QColor("#666666"))

        p = self.canvas_container.pos()
        self.shadow.setPixmap(self.pixmap)
        self.shadow.move(p.x() + 2, p.y() + 2)
        self.shadow.setMinimumSize(w, h)
        self.shadow.setMaximumSize(w, h)
        self.shadow.setGraphicsEffect(QtWidgets.QGraphicsBlurEffect())

        self.pixmap2 = QtGui.QPixmap(w + 2, h + 2)
        self.pixmap2.fill(QtGui.QColor("#666666"))

        p = self.canvas_container.pos()
        self.canvas_border.setPixmap(self.pixmap2)
        self.canvas_border.move(p.x() - 1, p.y() - 1)
        self.canvas_border.setMinimumSize(w + 2, h + 2)
        self.canvas_border.setMaximumSize(w + 2, h + 2)

    def fitToView(self, change_dpi: bool = False):
        """ fit the figure to the view """
        self.fitted_to_view = True
        if change_dpi:
            w, h = self.canvas.get_width_height()
            factor = min((self.canvas_canvas.width() - 30) / w, (self.canvas_canvas.height() - 30) / h)
            self.fig.set_dpi(self.fig.get_dpi() * factor)
            self.fig.canvas.draw()

            self.canvas.updateGeometry()
            w, h = self.canvas.get_width_height()
            self.canvas_container.setMinimumSize(w, h)
            self.canvas_container.setMaximumSize(w, h)

            self.canvas_container.move(int((self.canvas_canvas.width() - w) / 2 + 10),
                                       int((self.canvas_canvas.height() - h) / 2 + 10))

            self.updateRuler()
            self.fig.canvas.draw()

        else:
            w, h = self.canvas.get_width_height()
            self.canvas_canvas.setMinimumWidth(w + 30)
            self.canvas_canvas.setMinimumHeight(h + 30)

            self.canvas_container.move(int((self.canvas_canvas.width() - w) / 2 + 5),
                                       int((self.canvas_canvas.height() - h) / 2 + 5))
            self.updateRuler()

    def canvas_key_press(self, event: QtCore.QEvent):
        """ when a key in the canvas widget is pressed """
        if event.key == "control":
            self.control_modifier = True

    def canvas_key_release(self, event: QtCore.QEvent):
        """ when a key in the canvas widget is released """
        if event.key == "control":
            self.control_modifier = False

    def moveCanvasCanvas(self, offset_x: float, offset_y: float):
        """ when the canvas is panned """
        p = self.canvas_container.pos()
        self.canvas_container.move(int(p.x() + offset_x), int(p.y() + offset_y))

        self.updateRuler()

    def scroll_event(self, event: QtCore.QEvent):
        """ when the mouse wheel is used to zoom the figure """
        if self.control_modifier:
            new_dpi = self.fig.get_dpi() + 10 * event.step

            self.fig.figure_dragger.select_element(None)

            pos = self.fig.transFigure.inverted().transform((event.x, event.y))
            pos_ax = self.fig.transFigure.transform(self.fig.axes[0].get_position())[0]

            self.fig.set_dpi(new_dpi)
            self.fig.canvas.draw()

            self.canvas.updateGeometry()
            w, h = self.canvas.get_width_height()
            self.canvas_container.setMinimumSize(w, h)
            self.canvas_container.setMaximumSize(w, h)

            pos2 = self.fig.transFigure.transform(pos)
            diff = np.array([event.x, event.y]) - pos2

            pos_ax2 = self.fig.transFigure.transform(self.fig.axes[0].get_position())[0]
            diff += pos_ax2 - pos_ax
            self.moveCanvasCanvas(*diff)

            bb = self.fig.axes[0].get_position()

    def resizeEvent(self, event: QtCore.QEvent):
        """ when the window is resized """
        if self.fitted_to_view:
            self.fitToView(True)
        else:
            self.updateRuler()

    def showEvent(self, event: QtCore.QEvent):
        """ when the window is shown """
        self.fitToView(True)
        self.updateRuler()

    def button_press_event(self, event: QtCore.QEvent):
        """ when a mouse button is pressed """
        if event.button == 2:
            self.drag = np.array([event.x, event.y])

    def mouse_move_event(self, event: QtCore.QEvent):
        """ when the mouse is moved """
        if self.drag is not None:
            pos = np.array([event.x, event.y])
            offset = pos - self.drag
            offset[1] = -offset[1]
            self.moveCanvasCanvas(*offset)
        trans = transforms.Affine2D().scale(2.54, 2.54) + self.fig.dpi_scale_trans.inverted()
        pos = trans.transform((event.x, event.y))
        self.footer_label.setText("%.2f, %.2f (cm) [%d, %d]" % (pos[0], pos[1], event.x, event.y))

        if event.ydata is not None:
            self.footer_label2.setText("%.2f, %.2f" % (event.xdata, event.ydata))
        else:
            self.footer_label2.setText("")

    def button_release_event(self, event: QtCore.QEvent):
        """ when the mouse button is released """
        if event.button == 2:
            self.drag = None

    def keyPressEvent(self, event: QtCore.QEvent):
        """ when a key is pressed """
        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = True
        if event.key() == QtCore.Qt.Key_Left:
            self.moveCanvasCanvas(-10, 0)
        if event.key() == QtCore.Qt.Key_Right:
            self.moveCanvasCanvas(10, 0)
        if event.key() == QtCore.Qt.Key_Up:
            self.moveCanvasCanvas(0, -10)
        if event.key() == QtCore.Qt.Key_Down:
            self.moveCanvasCanvas(0, 10)

        if event.key() == QtCore.Qt.Key_F:
            self.fitToView(True)

    def keyReleaseEvent(self, event: QtCore.QEvent):
        """ when a key is released """
        if event.key() == QtCore.Qt.Key_Control:
            self.control_modifier = False

    def updateFigureSize(self):
        """ update the size of the figure """
        w, h = self.canvas.get_width_height()
        self.canvas_container.setMinimumSize(w, h)
        self.canvas_container.setMaximumSize(w, h)

    def changedFigureSize(self, size: tuple):
        """ change the size of the figure """
        self.fig.set_size_inches(np.array(size) / 2.54)
        self.fig.canvas.draw()



class ToolBar(QtWidgets.QToolBar):

    def __init__(self, canvas: Canvas, figure: Figure):
        """ A widget that displays a toolbar similar to the default Matplotlib toolbar (for the zoom and pan tool)

        Args:
            canvas: the canvas of the figure
            figure: the figure
        """
        super().__init__()
        self.canvas = canvas
        self.fig = figure
        self.navi_toolbar = NavigationToolbar(self.canvas, self)
        self.navi_toolbar.hide()

        self._actions = self.navi_toolbar._actions
        self._actions["home"] = self.addAction(self.navi_toolbar._icon("home.png"), "", self.navi_toolbar.home)

        self._actions["back"] = self.addAction(self.navi_toolbar._icon("back.png"), "", self.navi_toolbar.back)

        self._actions["forward"] = self.addAction(self.navi_toolbar._icon("forward.png"), "", self.navi_toolbar.forward)
        self.addSeparator()

        # the action group makes the actions exclusive, you
        # can't use 2 at the same time
        action_group = QtWidgets.QActionGroup(self)

        self._actions["drag"] = self.addAction(self.icon("arrow.png"), "", self.setSelect)
        self._actions["drag"].setCheckable(True)
        self._actions["drag"].setActionGroup(action_group)

        self._actions["pan"] = self.addAction(self.navi_toolbar._icon("move.png"), "", self.setPan)
        self._actions["pan"].setCheckable(True)
        self._actions["pan"].setActionGroup(action_group)

        self._actions["zoom"] = self.addAction(self.navi_toolbar._icon("zoom_to_rect.png"), "", self.setZoom)
        self._actions["zoom"].setCheckable(True)
        self._actions["zoom"].setActionGroup(action_group)

        self.navi_toolbar._active = 'DRAG'
        self._actions['drag'].setChecked(True)
        self.prev_active = 'DRAG'

    def icon(self, name: str):
        """ get an icon with the given filename """
        pm = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), "..","icons", name))
        if hasattr(pm, 'setDevicePixelRatio'):
            try:  # older mpl < 3.5.0
                pm.setDevicePixelRatio(self.canvas._dpi_ratio)
            except AttributeError:
                pm.setDevicePixelRatio(self.canvas.device_pixel_ratio)

        return QtGui.QIcon(pm)

    def setSelect(self):
        """ select the pylustrator selection and drag tool """
        self.fig.figure_dragger.activate()

        if self.prev_active=="PAN":
            self.navi_toolbar.pan()
        elif self.prev_active=="ZOOM":
            self.navi_toolbar.zoom()

        self.prev_active = 'DRAG'

        self.navi_toolbar._active = 'DRAG'

    def setPan(self):
        """ select the mpl pan tool """
        if self.prev_active == "DRAG":
            self.fig.figure_dragger.deactivate()

        if self.navi_toolbar._active != 'PAN':
            self.navi_toolbar.pan()

        self.prev_active = 'PAN'

    def setZoom(self):
        """ select the mpl zoom tool """
        if self.prev_active == "DRAG":
            self.fig.figure_dragger.deactivate()

        if self.navi_toolbar._active != 'ZOOM':
            self.navi_toolbar.zoom()

        self.prev_active = 'ZOOM'

class PlotLayout(QtWidgets.QWidget):
    toolbar = None

    def __init__(self, signals: "Signals"):
        super().__init__()
        self.setMinimumSize(600, 500)

        signals.figure_changed.connect(self.setFigure)
        signals.canvas_changed.connect(self.setCanvas)

        self.layout_plot = QtWidgets.QVBoxLayout(self)
        self.layout_plot.setContentsMargins(0, 0, 0, 0)
        self.layout_plot.setSpacing(0)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        self.canvas_canvas = Canvas(signals)
        self.layout_plot.addWidget(self.canvas_canvas)

        self.footer_layout = QtWidgets.QHBoxLayout()
        self.layout_plot.addLayout(self.footer_layout)

        self.footer_label = QtWidgets.QLabel("")
        self.footer_layout.addWidget(self.footer_label)

        self.footer_layout.addStretch()

        self.footer_label2 = QtWidgets.QLabel("")
        self.footer_layout.addWidget(self.footer_label2)
        self.canvas_canvas.setFooters(self.footer_label, self.footer_label2)

    def setFigure(self, figure):
        self.figure = figure

    def setCanvas(self, canvas):
        self.layout_plot.removeItem(self.footer_layout)
        if self.toolbar is not None:
            self.layout_plot.removeWidget(self.toolbar)
            self.toolbar.setVisible(False)
            self.toolbar = None
        if getattr(canvas, "pyl_toolbar", None) is None:
            self.toolbar = ToolBar(canvas, self.figure)
            canvas.pyl_toolbar = self.toolbar
        else:
            self.toolbar = canvas.pyl_toolbar
        self.layout_plot.addWidget(self.toolbar)

        self.layout_plot.addLayout(self.footer_layout)
