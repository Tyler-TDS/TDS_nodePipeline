import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFileDialog

from ui.graph_scene import GraphScene
from ui.graph_view import GraphView
from ui.property_panel import PropertyPanel
from ui.breadcrumb_label import BreadcrumbLabel


from ui.node_item import NodeItem
from core.scene_io import save_scene, load_scene

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TDS Vertical Node Graph")
        self.resize(1200, 800)

        self.current_file_path = None
        self.create_menus()

        self.scene = GraphScene()
        self.view = GraphView(self.scene)
        self.property_panel = PropertyPanel()

        self.current_scene = self.scene
        self.scene.main_window = self
        self.scene.selectionChanged.connect(self.on_selection_changed)


        self.breadcrumb_label = BreadcrumbLabel()
        self.breadcrumb_label.setText("Main Scene")
        self.breadcrumb_label.main_scene = self.scene
        self.breadcrumb_label.main_window = self
        self.breadcrumb_label.setFixedHeight(28)
        self.breadcrumb_label.setStyleSheet("""
            QLabel {
                background-color: #202020;
                color: #dddddd;
                padding-left: 10px;
                font-weight: bold;
                border-bottom: 1px solid #333333;
            }
        """)

        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.setSpacing(0)
        graph_layout.addWidget(self.breadcrumb_label)
        graph_layout.addWidget(self.view)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        main_layout.addWidget(graph_container)
        main_layout.addWidget(self.property_panel)

        self.setCentralWidget(central_widget)


        self.scene.breadcrumb_label = self.breadcrumb_label
        self.scene.update_breadcrumb()

    def create_menus(self):
        file_menu = self.menuBar().addMenu("File")

        new_action = file_menu.addAction("New")
        save_action = file_menu.addAction("Save")
        save_as_action = file_menu.addAction("Save As")
        load_action = file_menu.addAction("Load")

        new_action.triggered.connect(self.new_scene)
        save_action.triggered.connect(self.save_scene)
        save_as_action.triggered.connect(self.save_scene_as)
        load_action.triggered.connect(self.load_scene)

    def new_scene(self):
        self.scene = GraphScene()
        self.scene.scene_name = "Main Scene"
        self.scene.main_window = self
        self.scene.breadcrumb_label = self.breadcrumb_label

        self.breadcrumb_label.main_scene = self.scene
        self.breadcrumb_label.main_window = self

        self.current_file_path = None
        self.set_current_scene(self.scene)
        self.property_panel.set_node_item(None)

    def save_scene(self):
        if not self.current_file_path:
            self.save_scene_as()
            return

        save_scene(self.scene, self.current_file_path)

    def save_scene_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Graph",
            "",
            "TDS Graph (*.tdsgraph)"
        )

        if not file_path:
            return

        if not file_path.endswith(".tdsgraph"):
            file_path += ".tdsgraph"

        self.current_file_path = file_path
        save_scene(self.scene, self.current_file_path)

    def load_scene(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Graph",
            "",
            "TDS Graph (*.tdsgraph)"
        )

        if not file_path:
            return

        loaded_scene = load_scene(file_path)

        self.scene = loaded_scene
        self.scene.main_window = self
        self.scene.breadcrumb_label = self.breadcrumb_label

        self.breadcrumb_label.main_scene = self.scene
        self.breadcrumb_label.main_window = self

        self.current_file_path = file_path

        self.set_current_scene(self.scene)
        self.property_panel.set_node_item(None)

    def on_selection_changed(self):
        scene = getattr(self, "current_scene", self.scene)

        active_item = getattr(scene, "last_selected_node_item", None)

        if active_item and active_item.isSelected():
            self.property_panel.set_node_item(active_item)
            return

        selected_items = scene.selectedItems()

        for item in selected_items:
            if isinstance(item, NodeItem):
                self.property_panel.set_node_item(item)
                return

        self.property_panel.set_node_item(None)

    def set_current_scene(self, scene):
        old_scene = getattr(self, "current_scene", None)

        if old_scene:
            try:
                old_scene.selectionChanged.disconnect(self.on_selection_changed)
            except TypeError:
                pass

        self.current_scene = scene
        scene.main_window = self

        try:
            scene.selectionChanged.disconnect(self.on_selection_changed)
        except TypeError:
            pass

        scene.selectionChanged.connect(self.on_selection_changed)

        self.view.setScene(scene)
        self.view.setFocus()
        scene.update_breadcrumb()
        self.property_panel.set_node_item(None)
        self.on_selection_changed()

    def create_test_nodes(self):
        root_node = RootNode()
        root_item = NodeItem(root_node)
        root_item.setPos(100, 100)
        self.scene.addItem(root_item)

        entity_node = EntityNode()
        entity_item = NodeItem(entity_node)
        entity_item.setPos(100, 300)
        self.scene.addItem(entity_item)

        task_node = TaskNode()
        task_item = NodeItem(task_node)
        task_item.setPos(100, 500)
        self.scene.addItem(task_item)

        print_node = PrintNode()
        print_item = NodeItem(print_node)
        print_item.setPos(100, 700)
        self.scene.addItem(print_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())