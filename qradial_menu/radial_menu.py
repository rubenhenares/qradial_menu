# *********************************************************************
# +++ IMPORTS
# *********************************************************************
import math
from PyQt5 import QtWidgets, QtCore, QtGui


# *********************************************************************
# +++ CLASS
# *********************************************************************
class RadialMenu(QtWidgets.QWidget):

    # =====================================================================
    # +++ CONSTRUCTOR
    # =====================================================================
    def __init__(self, radius_=128.0, thickness_=48.0, icon_size_=36.0, parent=None):
        super(RadialMenu, self).__init__(parent)

        self._radius = radius_
        self._thickness = thickness_
        self._icon_size = icon_size_
        self._cancel_radius = 0.0

        self._font = QtGui.QFont("Arial", 10)

        self._actions = []

        self._mouse_pos = None
        self._hover_index = -1

        self._update_geometry()
        self.hide()

    # =====================================================================
    # +++ PROPERTIES
    # =====================================================================
    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        self._update_geometry()

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, value):
        self._thickness = value
        self._update_geometry()

    @property
    def icon_size(self):
        return self._icon_size

    @icon_size.setter
    def icon_size(self, value):
        self._icon_size = value

    # =====================================================================
    # +++ PRIVATE METHODS
    # =====================================================================
    def _update_geometry(self):
        self._bbox = QtCore.QRectF(0, 0, self._radius * 2.0, self._radius * 2.0)
        self._arc_bbox = QtCore.QRectF(self._thickness / 2.0, self._thickness / 2.0,
                                       self._radius * 2.0 - self._thickness, self._radius * 2.0 - self._thickness)

        self._label_bbox = QtCore.QRectF(self._arc_bbox.x() + self._thickness / 2.0,
                                         self._arc_bbox.y() + self._thickness / 2.0,
                                         self._arc_bbox.width() - self._thickness,
                                         self._arc_bbox.height() - self._thickness)

        self._arc_margin = (1.0 / self._radius) * 100.0
        self._cancel_radius = (self._radius - self._thickness / 2.0) * .25

        self.setFixedWidth(self._radius * 2.0 + self._thickness)
        self.setFixedHeight(self._radius * 2.0 + self._thickness)
        self.update()

    def _update_step(self):
        self._arc_step = int(360.0 / len(self._actions))

    def _update_hover_index(self):
        centered_position = self._mouse_pos - self._bbox.center()
        radius, radians, degrees = self._cartesian_to_polar(centered_position)

        if radius > self._cancel_radius:
            self._hover_index = math.floor(degrees / self._arc_step)
        else:
            self._hover_index = -1

    def _degrees_to_cartesian(self, radius, degrees):
        radians = ((math.pi * 2.0) / 360.0) * degrees
        return self._radians_to_cartesian(radius, radians)

    def _radians_to_cartesian(self, radius, degrees):
        result = QtCore.QPointF(radius * math.cos(degrees),
                                radius * math.sin(degrees))

        result.setX(result.x() + self.width() / 2.0 - self._thickness / 2.0)
        result.setY(result.y() + self.height() / 2.0 - self._thickness / 2.0)
        return result

    def _cartesian_to_polar(self, cartesian, direction=-1):
        radius = math.sqrt(cartesian.x() ** 2 + cartesian.y() ** 2)

        try:
            radians = math.atan2(cartesian.y(), cartesian.x())
            degrees = math.degrees(radians)
            degrees = 360.0 + degrees if degrees < 0.0 else degrees

            if direction == -1:
                degrees = 360.0 - degrees

            degrees = min(degrees, 359.0)

        except ValueError:
            radians = 0.0
            degrees = 0.0

        return radius, radians, degrees

    # =====================================================================
    # +++ PUBLIC METHODS
    # =====================================================================
    def add_action(self, action):
        self._actions.append(action)
        self._update_step()

    def remove_action(self, action):
        if action in self._actions:
            self._actions.remove(action)
            self._update_step()

    def action(self, index):
        if len(self._actions) > index > -1:
            return self._actions[index]

    def popup(self, position):
        # TODO: Override show?
        position.setX(position.x() - self._bbox.width() / 2.0)
        position.setY(position.y() - self._bbox.height() / 2.0)
        self.move(position)

        self.show()
        self.grabMouse()

    def close(self):
        if self._hover_index > -1:
            self._actions[self._hover_index].trigger()

        self._hover_index = -1
        self.hide()
        self.releaseMouse()
        self._mouse_pos = None

    # =====================================================================
    # +++ OVERRIDES
    # =====================================================================
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.RightButton:
            self.close()

    def mouseMoveEvent(self, event):
        self._mouse_pos = event.pos()
        self._update_hover_index()

    def wheelEvent(self, event):
        angle_delta = event.angleDelta() * (1.0 / 8.0)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)

        # Draw arcs
        arc_pen = QtGui.QPen(QtCore.Qt.black, self._thickness)
        arc_pen.setCapStyle(QtCore.Qt.FlatCap)
        painter.setPen(arc_pen)
        painter.setOpacity(0.35)

        for index, action in enumerate(self._actions):
            painter.drawArc(self._arc_bbox, index * self._arc_step * 16, (self._arc_step - self._arc_margin) * 16)

        # Draw hover elements
        if self._hover_index > -1:

            # arc
            arc_hover_pen = QtGui.QPen(QtCore.Qt.white, self._thickness)
            arc_hover_pen.setCapStyle(QtCore.Qt.FlatCap)

            painter.setPen(arc_hover_pen)
            painter.setOpacity(0.55)

            painter.drawArc(self._arc_bbox, self._hover_index * self._arc_step * 16, (self._arc_step - self._arc_margin) * 16)

            # text
            label_pen = QtGui.QPen(QtCore.Qt.black, 1.0)
            painter.setPen(label_pen)
            painter.setFont(self._font)
            painter.setOpacity(1.0)

            painter.drawText(self._label_bbox,
                             QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter,
                             self._actions[self._hover_index].text())

        # Draw icons
        painter.setOpacity(1.0)
        for index, action in enumerate(self._actions):
            if action.icon():
                pixmap = action.icon().pixmap(self._icon_size)
                pixmap_degrees = index * self._arc_step - self._arc_step / 2.0
                pixmap_position = self._degrees_to_cartesian(self._radius - self._thickness / 2.0, pixmap_degrees)
                pixmap_position.setX(pixmap_position.x() - self._icon_size / 2.0)
                pixmap_position.setY(pixmap_position.y() - self._icon_size / 2.0)
                painter.drawPixmap(pixmap_position, pixmap)

        # Draw text

        # DEBUG
        if False:
            debug_brush = QtGui.QBrush(QtCore.Qt.red)

            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(debug_brush)
            painter.setOpacity(0.25)
            painter.drawRect(self._bbox)

            arc_pen = QtGui.QPen(QtCore.Qt.blue, self._thickness)
            arc_pen.setCapStyle(QtCore.Qt.FlatCap)
            painter.setPen(arc_pen)
            painter.setOpacity(1.0)
            painter.drawArc(self._arc_bbox, 0 * self._arc_step * 16, -self._arc_step * 16)
