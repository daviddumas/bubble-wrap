from PyQt5.QtCore import *
from PyQt5.QtGui import *
import math


class BaseWidget:
    def __init__(self, image_src=None, source=None, target=None, image2_src=None):
        self.image = QImage(image_src)
        self.image2 = None if image2_src is None else QImage(image2_src)
        self.source = source
        self.target = target
        self.hit = False

    @property
    def center(self):
        assert self.target is not None
        return self.target.center().x(), self.target.center().y()

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
        if self.hit and self.image2 is not None:
            QPainter.drawImage(self.target, self.image2, self.source)
        else:
            QPainter.drawImage(self.target, self.image, self.source)

    def setPos(self, x, y):
        self.target = QRectF(x, y, self.width, self.height)

    def isHit(self, mouse):
        self.hit = self.target.contains(mouse.pos().x(), mouse.pos().y())
        return self.hit

    def release(self):
        self.hit = False


class TranslateWidget(BaseWidget):
    RIGHT = 1
    UP = 2
    LEFT = 3
    DOWN = 4

    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__("ui/assets/dpad_norm.png", QRectF(0,0,52,52), targetQRect)
        self.current_act = 0

    def draw(self, QPainter):
        if self.current_act==0:
            super().draw(QPainter)
        elif(self.current_act==1):
            QPainter.drawImage(self.target, QImage("ui/assets/dpad_right.png"), self.source)
        elif(self.current_act==2):
            QPainter.drawImage(self.target, QImage("ui/assets/dpad_up.png"), self.source)
        elif(self.current_act==3):
            QPainter.drawImage(self.target, QImage("ui/assets/dpad_left.png"), self.source)
        elif(self.current_act==4):
            QPainter.drawImage(self.target, QImage("ui/assets/dpad_down.png"), self.source)

    def isHit(self, mouse):
        if super().isHit(mouse):
            a45 = 0.785398
            a90 = 1.570796
            angle = math.atan2(self.center[1]-mouse.pos().y(), mouse.pos().x()-self.center[0])
            if a45 > angle >= -a45:
                self.current_act = 1
                return self.RIGHT
            elif a45+a90 > angle >= a45:
                self.current_act = 2
                return self.UP
            elif a45+a90 <= angle or -a45-a90 >= angle:
                self.current_act = 3
                return self.LEFT
            else:
                self.current_act = 4
                return self.DOWN
        else:
            self.current_act = 0
            return False

    def release(self):
        self.current_act = 0

class PlusWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__("ui/assets/plus_norm.png", QRectF(0,0,22,22), targetQRect, image2_src="ui/assets/plus_act.png")

class MinusWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__("ui/assets/minus_norm.png", QRectF(0,0,22,22), targetQRect, image2_src="ui/assets/minus_act.png")