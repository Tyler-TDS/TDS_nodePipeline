from PyQt5.QtWidgets import QGraphicsPathItem
from PyQt5.QtGui import QPainterPath, QPen, QColor
from PyQt5.QtCore import Qt


class EdgeItem(QGraphicsPathItem):
    def __init__(self, start_node, start_socket_index, end_node=None, end_socket_index=None):
        super().__init__()

        self.start_node = start_node
        self.start_socket_index = start_socket_index

        self.end_node = end_node
        self.end_socket_index = end_socket_index

        self.temp_end_pos = None

        self.setZValue(-1)

        self.default_pen = QPen(QColor(180, 180, 180), 2)
        self.selected_pen = QPen(QColor(220, 120, 120), 3)

        self.setPen(self.default_pen)

        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)

        self.update_path()

    def set_temp_end_pos(self, pos):
        self.temp_end_pos = pos
        self.update_path()

    def update_path(self):
        start = self.start_node.mapToScene(
            self.start_node.get_output_socket_pos(self.start_socket_index)
        )

        if self.end_node is not None:
            end = self.end_node.mapToScene(
                self.end_node.get_input_socket_pos(self.end_socket_index)
            )
        else:
            end = self.temp_end_pos or start

        path = QPainterPath(start)

        mid_y = (start.y() + end.y()) * 0.5

        path.cubicTo(
            start.x(), mid_y,
            end.x(), mid_y,
            end.x(), end.y()
        )

        self.setPath(path)

    def paint(self, painter, option, widget=None):
        self.setPen(self.selected_pen if self.isSelected() else self.default_pen)
        super().paint(painter, option, widget)