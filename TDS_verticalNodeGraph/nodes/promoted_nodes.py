import os
class PromotedInputNode:
    def __init__(
        self,
        parent_node=None,
        input_name="input",
        source_node_item=None,
        source_output_index=0,
    ):
        self.background_color = (0, 0, 90)

        self.parent_node = parent_node
        self.input_name = input_name

        self.source_node_item = source_node_item
        self.source_output_index = source_output_index

        self.inputs = []
        self.outputs = [
            input_name
        ]

        self.update_title()

    def update_title(self):
        if self.source_node_item:
            source_node = self.source_node_item.node
            source_title = getattr(source_node, "title", self.input_name)
            self.title = f"Input: {source_title}"
        else:
            self.title = f"Input: {self.input_name}"

    def evaluate(self):
        self.update_title()
        if not self.source_node_item:
            return {
                self.input_name: None
            }

        source_scene = self.source_node_item.scene()

        if not source_scene or not hasattr(source_scene, "evaluate_node_recursive"):
            return {
                self.input_name: None
            }

        source_node = self.source_node_item.node
        source_result = source_scene.evaluate_node_recursive(self.source_node_item)

        output_name = source_node.outputs[self.source_output_index]
        value = source_result.get(output_name)
        value = os.path.join(value, self.parent_node.title).replace("\\", "/")
        return {
            self.input_name: value
        }