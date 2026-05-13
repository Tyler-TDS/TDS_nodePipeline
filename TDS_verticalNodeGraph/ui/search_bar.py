from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal


class NodeSearchPopup(QWidget):
    node_selected = pyqtSignal(object)

    def __init__(self, node_classes):
        super().__init__()

        self.node_classes = node_classes
        self.filtered_classes = []
        self._accepted = False

        self.setWindowFlags(Qt.Popup)
        self.setFixedWidth(260)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search nodes...")

        self.list_widget = QListWidget()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        layout.addWidget(self.search)
        layout.addWidget(self.list_widget)

        self.search.textChanged.connect(self.refresh)

        # Do NOT also handle Enter in keyPressEvent.
        # This is the only Enter path.
        self.search.returnPressed.connect(self.accept_current)

        self.list_widget.itemClicked.connect(self.accept_item)

        self.refresh()

    def refresh(self):
        text = self.search.text().lower().strip()

        self.list_widget.clear()
        self.filtered_classes = []

        for node_class in self.node_classes:
            name = node_class.__name__.replace("Node", "")

            if text and text not in name.lower():
                continue

            self.filtered_classes.append(node_class)

            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, node_class)
            self.list_widget.addItem(item)

        if self.list_widget.count():
            self.list_widget.setCurrentRow(0)

    def accept_current(self):
        if self._accepted:
            return

        item = self.list_widget.currentItem()
        if not item:
            return

        self._accepted = True

        node_class = item.data(Qt.UserRole)
        self.node_selected.emit(node_class)
        self.close()

    def accept_item(self, item):
        if self._accepted:
            return

        self._accepted = True

        node_class = item.data(Qt.UserRole)
        self.node_selected.emit(node_class)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return

        if event.key() in (Qt.Key_Down, Qt.Key_Up):
            current = self.list_widget.currentRow()

            if event.key() == Qt.Key_Down:
                current += 1
            else:
                current -= 1

            current = max(0, min(current, self.list_widget.count() - 1))
            self.list_widget.setCurrentRow(current)

            event.accept()
            return

        # Do not handle Enter here.
        # QLineEdit.returnPressed already handles it.
        super().keyPressEvent(event)

    def show_at(self, global_pos):
        self._accepted = False
        self.move(global_pos)
        self.show()
        self.search.setFocus()
        self.search.selectAll()