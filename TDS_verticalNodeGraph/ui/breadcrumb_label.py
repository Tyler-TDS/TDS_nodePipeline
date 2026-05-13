from PyQt5.QtWidgets import QLabel


class BreadcrumbLabel(QLabel):
    def __init__(self):
        super().__init__()

        self.main_scene = None
        self.main_window = None

    def mousePressEvent(self, event):
        if self.main_scene and self.main_window:
            self.main_window.set_current_scene(self.main_scene)

        super().mousePressEvent(event)