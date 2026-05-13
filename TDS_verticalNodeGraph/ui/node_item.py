from PyQt5.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PyQt5.QtCore import QRectF, Qt, QPointF
from PyQt5.QtGui import QColor, QPen, QBrush, QFont


class NodeTitleItem(QGraphicsTextItem):
    def __init__(self, node_item):
        super().__init__(node_item)

        self.node_item = node_item
        self._editing = False

        self.setPlainText(self.node_item.node.title)
        self.setDefaultTextColor(QColor(230, 230, 230))
        self.setFont(QFont("Arial", 11, QFont.Bold))
        self.setTextWidth(-1)
        self.setTextInteractionFlags(Qt.NoTextInteraction)

        option = self.document().defaultTextOption()
        option.setAlignment(Qt.AlignCenter)
        self.document().setDefaultTextOption(option)

    def start_edit(self):
        if self._editing:
            return

        self._editing = True
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus(Qt.MouseFocusReason)

        cursor = self.textCursor()
        cursor.select(cursor.Document)
        self.setTextCursor(cursor)

    def finish_edit(self):
        if not self._editing:
            return

        self._editing = False
        self.setTextInteractionFlags(Qt.NoTextInteraction)

        text = self.toPlainText().strip() or "Node"
        self.setPlainText(text)
        self.node_item.node.title = text

        self.node_item.update_title_position()
        self.node_item.update()

    def focusOutEvent(self, event):
        self.finish_edit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.finish_edit()
            event.accept()
            return

        super().keyPressEvent(event)


class NodeItem(QGraphicsItem):
    def __init__(self, node):
        super().__init__()

        self.node = node

        self.width = 140
        self.height = 60
        self.socket_radius = 6

        self.edges = []

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        self.title_item = NodeTitleItem(self)
        self.update_title_position()

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def update_title_position(self):
        title_rect = self.title_item.boundingRect()

        x = (self.width - title_rect.width()) / 2
        y = (self.height - title_rect.height()) / 2

        self.title_item.setPos(x, y)

    def get_input_socket_pos(self, index):
        count = max(len(getattr(self.node, "inputs", [])), 1)
        spacing = self.width / (count + 1)
        return QPointF(spacing * (index + 1), 0)

    def get_output_socket_pos(self, index):
        count = max(len(getattr(self.node, "outputs", [])), 1)
        spacing = self.width / (count + 1)
        return QPointF(spacing * (index + 1), self.height)

    def get_socket_at(self, pos):
        for index in range(len(getattr(self.node, "inputs", []))):
            socket_pos = self.get_input_socket_pos(index)
            if (pos - socket_pos).manhattanLength() <= self.socket_radius * 2:
                return "input", index

        for index in range(len(getattr(self.node, "outputs", []))):
            socket_pos = self.get_output_socket_pos(index)
            if (pos - socket_pos).manhattanLength() <= self.socket_radius * 2:
                return "output", index

        return None, None

    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_path()

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        title_rect = self.title_item.mapRectToParent(
            self.title_item.boundingRect()
        )

        if title_rect.contains(event.pos()):
            self.title_item.start_edit()
            event.accept()
            return

        if getattr(self.node, "can_enter", False):
            scene = self.scene()

            if scene and hasattr(scene, "enter_node"):
                scene.enter_node(self)
                event.accept()
                return

        event.accept()

    def paint(self, painter, option, widget=None):
        rect = self.boundingRect()

        color = getattr(self.node, "background_color", (45, 45, 45))
        body_color = QColor(*color)

        border_color = QColor(90, 90, 90)
        socket_color = QColor(130, 130, 130)

        if self.isSelected():
            border_color = QColor(120, 160, 220)

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(body_color))
        painter.drawRoundedRect(rect, 10, 10)

        painter.setBrush(QBrush(socket_color))
        painter.setPen(Qt.NoPen)

        for index in range(len(getattr(self.node, "inputs", []))):
            pos = self.get_input_socket_pos(index)
            painter.drawEllipse(pos, self.socket_radius, self.socket_radius)

        for index in range(len(getattr(self.node, "outputs", []))):
            pos = self.get_output_socket_pos(index)
            painter.drawEllipse(pos, self.socket_radius, self.socket_radius)