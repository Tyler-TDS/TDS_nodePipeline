from core.socket import Socket

class Node:
    def __init__(self, title="Node"):
        self.title = title
        self.inputs = []
        self.outputs = []

    def add_input(self, name, socket_type="any"):
        socket = Socket(name, socket_type, is_input=True)
        self.inputs.append(socket)
        return socket

    def add_output(self, name, socket_type="any"):
        socket = Socket(name, socket_type, is_input=False)
        self.outputs.append(socket)
        return socket