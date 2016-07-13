from PyQt5.QtCore import *
from PyQt5.QtGui import *


class BaseWidget:
    def __init__(self, image_src=None, source=None, target=None):
        self.image = QImage(image_src)
        self.source = source
        self.target = target

    @property
    def height(self):
        assert self.source is not None
        return self.source.height()

    @property
    def width(self):
        assert self.source is not None
        return self.source.width()

    def draw(self, QPainter):
        assert self.image is not None
        QPainter.drawImage(self.target, self.image, self.source)

    def setPos(self, x, y):
        self.target = QRectF(x, y, self.width, self.height)

    def isHit(self, mouse):
        return self.target.contains(mouse.pos().x(), mouse.pos().y())


class TranslateWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__("ui/assets/dpad.png", QRectF(0,0,52,52), targetQRect)

class PlusWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__("ui/assets/more.png", QRectF(0,0,22,22), targetQRect)

class MinusWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__("ui/assets/less.png", QRectF(0,0,22,22), targetQRect)