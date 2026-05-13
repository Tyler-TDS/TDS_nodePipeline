from nodes.root_nodes import RootNode, EntityNode, TaskNode, FolderNode
from nodes.debug_nodes import PrintNode
from nodes.promoted_nodes import PromotedInputNode


NODE_REGISTRY = {
    "Root": RootNode,
    "Task": TaskNode,
    "Entity": EntityNode,
    "Folder": FolderNode,
    "Print": PrintNode,
    "PromotedInput": PromotedInputNode,
}

def get_node_class_by_type(type_name):
    for node_class in NODE_REGISTRY.values():
        if node_class.__name__ == type_name:
            return node_class

    raise ValueError(f"Unknown node type: {type_name}")

def get_node_classes():
    # Do not show PromotedInputNode in the Tab search.
    return [
        RootNode,
        EntityNode,
        FolderNode,
        TaskNode,
        PrintNode,
    ]


def get_node_names():
    return list(NODE_REGISTRY.keys())


def create_node(name):
    return NODE_REGISTRY[name]()