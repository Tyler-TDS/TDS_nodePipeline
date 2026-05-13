from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt, QLineF
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen

from nodes.registry import get_node_classes
from ui.node_item import NodeItem
from ui.search_bar import NodeSearchPopup


class GraphView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)

        self.setFocusPolicy(Qt.StrongFocus)

        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self.setDragMode(QGraphicsView.NoDrag)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._panning = False
        self._last_pan_pos = None

        self.node_classes = get_node_classes()
        self.node_search_popup = None
        self.last_mouse_scene_pos = None

    def event(self, event):
        if event.type() == event.KeyPress and event.key() == Qt.Key_Tab:
            self.setFocus()
            self.open_node_search()
            event.accept()
            return True

        return super().event(event)
    def contextMenuEvent(self, event):
        event.accept()

    def focusNextPrevChild(self, next):
        return False


    def mousePressEvent(self, event):
        self.setFocus()

        if event.button() == Qt.RightButton:
            event.accept()
            return

        if event.button() == Qt.MiddleButton:
            self._panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())

            # Walk up to the actual NodeItem if we clicked child text.
            node_item = item
            while node_item is not None and not isinstance(node_item, NodeItem):
                node_item = node_item.parentItem()

            if event.modifiers() & Qt.ShiftModifier:
                if node_item:
                    node_item.setSelected(not node_item.isSelected())

                    if node_item.isSelected():
                        scene = self.scene()
                        if hasattr(scene, "set_active_node_item"):
                            scene.set_active_node_item(node_item)

                    event.accept()
                    return

            if item is None:
                self.setDragMode(QGraphicsView.RubberBandDrag)
            else:
                self.setDragMode(QGraphicsView.NoDrag)

        if node_item:
            scene = self.scene()
            if hasattr(scene, "set_active_node_item"):
                scene.set_active_node_item(node_item)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.last_mouse_scene_pos = self.mapToScene(event.pos())

        if self._panning:
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self._last_pan_pos = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            self.setDragMode(QGraphicsView.NoDrag)

        super().mouseReleaseEvent(event)

    def open_node_search(self):
        if self.node_search_popup:
            self.node_search_popup.close()

        self.node_search_popup = NodeSearchPopup(self.node_classes)

        scene_pos = self.last_mouse_scene_pos or self.mapToScene(
            self.viewport().rect().center()
        )

        global_pos = self.mapToGlobal(self.mapFromScene(scene_pos))

        self.node_search_popup.node_selected.connect(
            lambda node_class, scene_pos=scene_pos: self.add_node_from_search(
                node_class,
                scene_pos
            )
        )

        self.node_search_popup.show_at(global_pos)

    def add_node_from_search(self, node_class, scene_pos):
        node = node_class()

        node_item = NodeItem(node)
        node_item.setPos(scene_pos)

        self.scene().addItem(node_item)
        self.scene().clearSelection()
        node_item.setSelected(True)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        grid_size = 40

        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)

        pen = QPen(QColor(45, 45, 45))
        pen.setWidth(1)
        painter.setPen(pen)

        x = left
        while x < rect.right():
            painter.drawLine(QLineF(x, rect.top(), x, rect.bottom()))
            x += grid_size

        y = top
        while y < rect.bottom():
            painter.drawLine(QLineF(rect.left(), y, rect.right(), y))
            y += grid_size

    def wheelEvent(self, event):
        zoom_factor = 1.15

        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)