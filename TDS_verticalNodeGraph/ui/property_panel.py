from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
)
from PyQt5.QtCore import Qt


class PropertyPanel(QWidget):
    def __init__(self):
        super().__init__()

        self.node_item = None
        self.editors = {}

        self.setFixedWidth(280)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.title_label = QLabel("Properties")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.form_layout = QFormLayout()

        self.evaluate_button = QPushButton("Evaluate")
        self.evaluate_button.clicked.connect(self.evaluate_node)
        self.main_layout.addWidget(self.evaluate_button)

        self.main_layout.addWidget(self.title_label)
        self.main_layout.addLayout(self.form_layout)

    def evaluate_node(self):
        if not self.node_item:
            return

        scene = self.node_item.scene()

        if scene and hasattr(scene, "evaluate_node"):
            scene.evaluate_node(self.node_item)

    def clear(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)

            widget = item.widget()
            if widget:
                widget.deleteLater()

            layout = item.layout()
            if layout:
                while layout.count():
                    child = layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        self.editors = {}

    def set_node_item(self, node_item):
        self.clear()
        self.node_item = node_item

        if not node_item:
            self.title_label.setText("Properties")
            return

        node = node_item.node
        self.title_label.setText(node.title)

        for prop_name in getattr(node, "editable_properties", []):
            value = getattr(node, prop_name, "")

            label = QLabel(self.format_label(prop_name))

            if isinstance(value, dict):
                checkbox_container = QWidget()
                checkbox_layout = QVBoxLayout(checkbox_container)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)

                for key, checked in value.items():
                    checkbox = QCheckBox(key)
                    checkbox.setChecked(bool(checked))
                    checkbox.stateChanged.connect(
                        lambda state, prop_name=prop_name, key=key: self.set_dict_property(
                            prop_name,
                            key,
                            state == Qt.Checked
                        )
                    )
                    checkbox_layout.addWidget(checkbox)

                self.form_layout.addRow(label, checkbox_container)

            else:
                editor = QLineEdit(str(value))
                editor.editingFinished.connect(
                    lambda prop_name=prop_name, editor=editor: self.set_property(
                        prop_name,
                        editor.text()
                    )
                )

                self.form_layout.addRow(label, editor)
                self.editors[prop_name] = editor

    def set_dict_property(self, prop_name, key, value):
        if not self.node_item:
            return

        node = self.node_item.node

        prop = getattr(node, prop_name, {})
        prop[key] = value
        setattr(node, prop_name, prop)

        scene = self.node_item.scene()
        if scene and hasattr(scene, "evaluate_node"):
            scene.evaluate_node(self.node_item)
    def set_property(self, prop_name, value):
        if not self.node_item:
            return

        node = self.node_item.node

        setattr(node, prop_name, value)

        # Sync naming properties to the visible node title.
        if prop_name in ("task_name", "entity_name"):
            node.title = value or type(node).__name__.replace("Node", "")

        # Refresh title text.
        self.node_item.title_item.setPlainText(node.title)
        self.node_item.update_title_position()
        self.node_item.update()

        # Re-evaluate.
        scene = self.node_item.scene()
        if scene and hasattr(scene, "evaluate_node"):
            scene.evaluate_node(self.node_item)

        # Refresh breadcrumb if this node owns a subgraph.
        if hasattr(node, "sub_scene") and node.sub_scene:
            node_type = type(node).__name__.replace("Node", "")
            node.sub_scene.scene_name = f"{node_type}: {node.title}"

            current_scene = self.node_item.scene()
            if current_scene and hasattr(current_scene, "update_breadcrumb"):
                current_scene.update_breadcrumb()

    def format_label(self, name):
        return name.replace("_", " ").title()