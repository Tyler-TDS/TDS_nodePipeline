import json

from ui.node_item import NodeItem
from ui.edge_item import EdgeItem
from ui.graph_scene import GraphScene
from nodes.registry import get_node_class_by_type
from nodes.promoted_nodes import PromotedInputNode


SAVE_VERSION = 1


def serialize_node_item(node_item):
    node = node_item.node

    data = {
        "type": type(node).__name__,
        "title": getattr(node, "title", type(node).__name__),
        "pos": [
            node_item.pos().x(),
            node_item.pos().y(),
        ],
        "properties": {},
        "subgraph": None,
    }

    for prop_name in getattr(node, "editable_properties", []):
        data["properties"][prop_name] = getattr(node, prop_name, None)


    if isinstance(node, PromotedInputNode):
        data["properties"]["input_name"] = node.input_name
        data["properties"]["source_output_index"] = node.source_output_index

    if getattr(node, "sub_scene", None):
        data["subgraph"] = serialize_scene(node.sub_scene)

    return data


def serialize_edge_item(edge_item, node_items):
    return {
        "start_node": node_items.index(edge_item.start_node),
        "start_socket_index": edge_item.start_socket_index,
        "end_node": node_items.index(edge_item.end_node),
        "end_socket_index": edge_item.end_socket_index,
    }


def serialize_scene(scene):
    node_items = [
        item for item in scene.items()
        if isinstance(item, NodeItem)
    ]

    # Do NOT skip edges connected to PromotedInputNode
    edge_items = [
        item for item in scene.items()
        if isinstance(item, EdgeItem)
           and item.end_node is not None
           and item.start_node in node_items
           and item.end_node in node_items
    ]

    return {
        "scene_name": getattr(scene, "scene_name", "Main Scene"),
        "nodes": [
            serialize_node_item(node_item)
            for node_item in node_items
        ],
        "edges": [
            serialize_edge_item(edge_item, node_items)
            for edge_item in edge_items
        ],
    }


def save_scene(scene, file_path):
    data = {
        "version": SAVE_VERSION,
        "scene": serialize_scene(scene),
    }

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def create_node_item_from_data(node_data):
    node_class = get_node_class_by_type(node_data["type"])
    node = node_class()

    node.title = node_data.get("title", node.title)

    for prop_name, value in node_data.get("properties", {}).items():
        setattr(node, prop_name, value)

    if hasattr(node, "input_name"):
        node.outputs = [node.input_name]
        node.update_title()

    node_item = NodeItem(node)
    node_item.setPos(*node_data.get("pos", [0, 0]))

    return node_item


def deserialize_scene(scene_data, parent_scene=None, parent_node_item=None):
    scene = GraphScene()
    scene.scene_name = scene_data.get("scene_name", "Main Scene")
    scene.parent_scene = parent_scene
    scene.parent_node_item = parent_node_item

    node_items = []

    for node_data in scene_data.get("nodes", []):
        node_item = create_node_item_from_data(node_data)
        scene.addItem(node_item)
        node_items.append(node_item)

        subgraph_data = node_data.get("subgraph")
        if subgraph_data:
            node_item.node.sub_scene = deserialize_scene(
                subgraph_data,
                parent_scene=scene,
                parent_node_item=node_item,
            )

    for edge_data in scene_data.get("edges", []):
        start_node = node_items[edge_data["start_node"]]
        end_node = node_items[edge_data["end_node"]]

        edge = EdgeItem(
            start_node=start_node,
            start_socket_index=edge_data["start_socket_index"],
            end_node=end_node,
            end_socket_index=edge_data["end_socket_index"],
        )

        scene.addItem(edge)

        start_node.add_edge(edge)
        end_node.add_edge(edge)

    for node_item in node_items:
        if (
                hasattr(node_item.node, "ensure_promoted_inputs")
                and getattr(node_item.node, "sub_scene", None)
        ):
            node_item.node.ensure_promoted_inputs(
                node_item.node.sub_scene,
                node_item
            )

    return scene


def load_scene(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return deserialize_scene(data["scene"])