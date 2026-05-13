from PyQt5.QtWidgets import QGraphicsScene

from PyQt5.QtCore import Qt

from ui.node_item import NodeItem
from ui.edge_item import EdgeItem


class GraphScene(QGraphicsScene):
    def __init__(self):
        super().__init__()

        self.setSceneRect(-5000, -5000, 10000, 10000)

        self.scene_name = "Main Scene"
        self.parent_scene = None
        self.parent_node_item = None
        self.breadcrumb_label = None

        self.active_edge = None
        self.active_output_node = None
        self.active_output_index = None

        self.last_selected_node_item = None

        self.socket_hit_radius = 22

    def set_active_node_item(self, node_item):
        self.last_selected_node_item = node_item
        self.selectionChanged.emit()

    def get_breadcrumb_parts(self):
        parts = []

        scene = self
        while scene is not None:
            parts.append(scene.scene_name)
            scene = scene.parent_scene

        return list(reversed(parts))

    def update_breadcrumb(self):
        root_scene = self

        while root_scene.parent_scene is not None:
            root_scene = root_scene.parent_scene

        label = getattr(root_scene, "breadcrumb_label", None)
        if not label:
            label = getattr(self, "breadcrumb_label", None)

        if label:
            label.setText(" > ".join(self.get_breadcrumb_parts()))

    def enter_node(self, node_item):
        node = node_item.node

        if not getattr(node, "sub_scene", None):
            node.sub_scene = GraphScene()
            node.sub_scene.parent_scene = self
            node.sub_scene.parent_node_item = node_item

            node_type = type(node).__name__.replace("Node", "")
            node.sub_scene.scene_name = f"{node_type}: {node.title}"

            if hasattr(node, "build_subgraph"):
                node.build_subgraph(node.sub_scene)

        if hasattr(node, "ensure_promoted_inputs"):
            node.ensure_promoted_inputs(node.sub_scene, node_item)

        from nodes.promoted_nodes import PromotedInputNode
        from ui.node_item import NodeItem

        for item in node.sub_scene.items():
            if not isinstance(item, NodeItem):
                continue

            if isinstance(item.node, PromotedInputNode):
                item.node.update_title()
                item.title_item.setPlainText(item.node.title)
                item.update_title_position()
                item.update()

        root_scene = self
        while root_scene.parent_scene is not None:
            root_scene = root_scene.parent_scene

        node.sub_scene.breadcrumb_label = root_scene.breadcrumb_label

        main_window = getattr(self, "main_window", None)

        if main_window:
            node.sub_scene.main_window = main_window
            main_window.set_current_scene(node.sub_scene)
        else:
            view = self.views()[0]
            view.setScene(node.sub_scene)
            node.sub_scene.update_breadcrumb()

    def find_socket_at(self, scene_pos, socket_type=None):
        for item in self.items():
            if not isinstance(item, NodeItem):
                continue

            if socket_type in (None, "input"):
                for index in range(len(item.node.inputs)):
                    socket_pos = item.mapToScene(item.get_input_socket_pos(index))

                    if (scene_pos - socket_pos).manhattanLength() <= self.socket_hit_radius:
                        return item, "input", index

            if socket_type in (None, "output"):
                for index in range(len(item.node.outputs)):
                    socket_pos = item.mapToScene(item.get_output_socket_pos(index))

                    if (scene_pos - socket_pos).manhattanLength() <= self.socket_hit_radius:
                        return item, "output", index

        return None, None, None

    def start_edge(self, node_item, socket_index, scene_pos):
        self.active_output_node = node_item
        self.active_output_index = socket_index

        self.active_edge = EdgeItem(
            start_node=node_item,
            start_socket_index=socket_index
        )

        self.active_edge.set_temp_end_pos(scene_pos)
        self.addItem(self.active_edge)

    def finish_edge(self, node_item, socket_index):
        self.active_edge.end_node = node_item
        self.active_edge.end_socket_index = socket_index
        self.active_edge.temp_end_pos = None
        self.active_edge.update_path()

        self.active_output_node.add_edge(self.active_edge)
        node_item.add_edge(self.active_edge)

        self.evaluate_node(node_item)
        self.active_edge = None
        self.active_output_node = None
        self.active_output_index = None

    def cancel_edge(self):
        if self.active_edge:
            self.removeItem(self.active_edge)

        self.active_edge = None
        self.active_output_node = None
        self.active_output_index = None

    def remove_edge(self, edge):
        if edge.start_node and edge in edge.start_node.edges:
            edge.start_node.edges.remove(edge)

        if edge.end_node and edge in edge.end_node.edges:
            edge.end_node.edges.remove(edge)

        self.removeItem(edge)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.parent_scene:
                main_window = getattr(self, "main_window", None)

                if main_window:
                    main_window.set_current_scene(self.parent_scene)
                else:
                    view = self.views()[0]
                    view.setScene(self.parent_scene)
                    self.parent_scene.update_breadcrumb()
                event.accept()
                return

        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for item in list(self.selectedItems()):
                if isinstance(item, EdgeItem):
                    self.remove_edge(item)

                elif isinstance(item, NodeItem):
                    self.remove_node(item)

            event.accept()
            return

        super().keyPressEvent(event)

    def remove_node(self, node_item, force=False):
        from nodes.promoted_nodes import PromotedInputNode

        if isinstance(node_item.node, PromotedInputNode) and not force:
            return

        for edge in list(node_item.edges):
            self.remove_edge(edge)

        self.removeItem(node_item)

    def evaluate_node(self, node_item):
        print('============ Evaluation ============')
        return self.evaluate_node_recursive(node_item)

    def evaluate_node_recursive(self, node_item):
        node = node_item.node

        input_values = {}

        for edge in node_item.edges:
            if edge.end_node != node_item:
                continue

            source_node_item = edge.start_node
            source_node = source_node_item.node

            source_result = self.evaluate_node_recursive(source_node_item)

            output_name = source_node.outputs[edge.start_socket_index]
            input_name = node.inputs[edge.end_socket_index]

            input_values[input_name] = source_result.get(output_name)

        if hasattr(node, "evaluate"):
            node._input_values = input_values
            return node.evaluate(**input_values)

        return {}

    def mousePressEvent(self, event):
        node_item, socket_type, socket_index = self.find_socket_at(event.scenePos())

        # Click output socket to start holding an edge
        if socket_type == "output":
            self.start_edge(node_item, socket_index, event.scenePos())
            event.accept()
            return

        # Click input socket while already holding edge to connect
        if self.active_edge and socket_type == "input":
            if node_item != self.active_output_node:
                self.finish_edge(node_item, socket_index)
            else:
                self.cancel_edge()

            event.accept()
            return

        # Click empty space while holding edge to cancel
        if self.active_edge:
            self.cancel_edge()
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.active_edge:
            self.active_edge.set_temp_end_pos(event.scenePos())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.active_edge:
            node_item, socket_type, socket_index = self.find_socket_at(
                event.scenePos(),
                socket_type="input"
            )

            # Drag-release onto input socket to connect
            if socket_type == "input" and node_item != self.active_output_node:
                self.finish_edge(node_item, socket_index)
                event.accept()
                return

            # Do NOT cancel here.
            # This allows click output -> release -> move -> click input.
            event.accept()
            return

        super().mouseReleaseEvent(event)