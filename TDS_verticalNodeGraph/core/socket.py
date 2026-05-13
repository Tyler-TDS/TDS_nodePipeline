
class Socket:
    def __init__(self, name, socket_type="any", is_input=True):
        self.name = name
        self.socket_type = socket_type
        self.is_input = is_input
