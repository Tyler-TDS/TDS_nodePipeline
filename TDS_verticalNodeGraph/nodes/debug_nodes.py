class PrintNode:
    def __init__(self):
        self.title = "Print"
        self.background_color = (45, 45, 45)

        self.inputs = [
            "value"
        ]

        self.outputs = []

    def evaluate(self, value=None):
        print("PRINT NODE:", value)
        return {}