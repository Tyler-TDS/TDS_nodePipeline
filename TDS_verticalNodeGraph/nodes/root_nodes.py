import os

class FolderNode:
    def __init__(self):
        self.title = "Folder"
        self.background_color = (45, 45, 45)

        self.root_variable = "project"

        self.editable_properties = [
            "root_variable"
        ]

        self.inputs = [
            "base_path",
        ]

        self.outputs = [
            "folder_path"
        ]

    def evaluate(self, base_path=None):
        base_path = base_path or ""

        token = f"{self.root_variable}"

        if base_path:
            folder_path = f"{base_path}/{token}"
        else:
            folder_path = token

        folder_path = folder_path.replace("\\", "/").replace("//", "/")
        return {
            "folder_path": folder_path
        }

class RootNode:
    def __init__(self):
        self.title = "Root"
        self.background_color = (90, 0, 0)

        self.base_path = "C:/projects"
        self.root_variable = "project"
        self.user_variable = "{user}"
        self.version_template = "v{number:03d}"
        self.date_template = "{DD/MM/YYYY}"

        self.editable_properties = [
            "base_path",
            "root_variable",
            "user_variable",
            "version_template",
            "date_template",
        ]

        self.inputs = []
        self.outputs = ["root_path"]

    def get_root_token(self):
        return "{" + self.root_variable + "}"

    def get_root_path(self):
        path = os.path.join(
            self.base_path,
            self.get_root_token()
        )

        return path.replace("\\", "/")

    def get_metadata(self):
        return {
            "base_path": self.base_path,
            "root_variable": self.root_variable,
            "root_path": self.get_root_path(),
            "user_variable": self.user_variable,
            "version_template": self.version_template,
            "date_template": self.date_template,
        }

    def evaluate(self):
        return {
            "root_path": self.get_root_path(),
            "user": self.user_variable,
            "version": self.version_template,
            "date": self.date_template,
        }


class EntityNode:
    def __init__(self):
        self.title = "Entity"
        self.background_color = (184, 174, 0)

        # Property shown in the property panel
        self.entity_name = ""

        self.editable_properties = [
            "entity_name",
        ]

        # One input and one output
        self.inputs = [
            "base_path",
        ]

        self.outputs = [
            "entity_path",
        ]

    def evaluate(self, base_path=None):
        base_path = base_path or ""

        token = f"{{{self.entity_name}}}"

        if base_path:
            entity_path = f"{base_path}/{token}"
        else:
            entity_path = token

        entity_path = entity_path.replace("\\", "/").replace("//", "/")
        return {
            "entity_path": entity_path,
        }



class TaskNode:
    def __init__(self):
        self.title = "Task"
        self.background_color = (0, 0, 90)

        self.can_enter = True
        self.sub_scene = None

        self.dcc_apps = {
            "Maya": False,
            "Houdini": False,
            "Nuke": False,
            "Blender": False,
            "Substance Painter": False,
        }

        self.task_name = ""
        self._input_values = {}
        self.editable_properties = [
            "task_name",
            "dcc_apps",
        ]

        self.inputs = [
            "base_path",
        ]

        self.outputs = [
            "task_path",
        ]

    def build_subgraph(self, scene):
        pass

    def ensure_promoted_inputs(self, scene, parent_node_item):
        from ui.node_item import NodeItem
        from nodes.promoted_nodes import PromotedInputNode

        if scene is None:
            return

        incoming_edges = [
            edge for edge in parent_node_item.edges
            if edge.end_node == parent_node_item
        ]

        valid_keys = set()

        for edge in incoming_edges:
            source_node = edge.start_node.node
            source_output_name = source_node.outputs[edge.start_socket_index]

            key = (
                id(edge.start_node),
                edge.start_socket_index,
                source_output_name,
            )

            valid_keys.add(key)

        promoted_items = [
            item for item in scene.items()
            if isinstance(item, NodeItem)
               and isinstance(item.node, PromotedInputNode)
        ]

        existing_by_key = {}

        for item in promoted_items:
            node = item.node

            key = (
                id(node.source_node_item),
                node.source_output_index,
                node.input_name,
            )

            # Remove invalid promoted nodes.
            if key not in valid_keys:
                scene.remove_node(item, force=True)
                continue

            # Remove duplicates with the same key.
            if key in existing_by_key:
                scene.remove_node(item, force=True)
                continue

            existing_by_key[key] = item

        y = 100

        for edge in incoming_edges:
            source_node = edge.start_node.node
            source_output_name = source_node.outputs[edge.start_socket_index]

            key = (
                id(edge.start_node),
                edge.start_socket_index,
                source_output_name,
            )

            if key in existing_by_key:
                promoted_item = existing_by_key[key]
                promoted_node = promoted_item.node

                promoted_node.parent_node = self
                promoted_node.source_node_item = edge.start_node
                promoted_node.source_output_index = edge.start_socket_index
                promoted_node.input_name = source_output_name
                promoted_node.outputs = [source_output_name]
                promoted_node.update_title()

                promoted_item.title_item.setPlainText(promoted_node.title)
                promoted_item.update_title_position()
                promoted_item.update()
                continue

            promoted_node = PromotedInputNode(
                parent_node=self,
                input_name=source_output_name,
                source_node_item=edge.start_node,
                source_output_index=edge.start_socket_index,
            )

            promoted_item = NodeItem(promoted_node)
            promoted_item.setPos(100, y)
            scene.addItem(promoted_item)

            existing_by_key[key] = promoted_item
            y += 140

    def evaluate(self, base_path=None):
        base_path = base_path or ""

        token = f"{{{self.task_name}}}"

        if base_path:
            task_path = f"{base_path}/{token}"
        else:
            task_path = token

        task_path = task_path.replace("\\", "/").replace("//", "/")

        return {
            "task_path": task_path,
        }