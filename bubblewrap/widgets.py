from PyQt5.QtCore import *
from PyQt5.QtGui import *
from collections import OrderedDict
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
        s = self.source
        if s is None:
            s = self.target
        assert s is not None
        return s.height()

    @property
    def width(self):
        s = self.source
        if s is None:
            s = self.target
        assert s is not None
        return s.width()

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

class InfoWidget(BaseWidget):
    def __init__(self):
        self.info_panels = OrderedDict()
        self.margins = 10
        self.font = QFont("Arial", 12)
        self.fm = QFontMetrics(self.font)
        self.max_width = 0
        super().__init__(target=QRectF(0,0,200,self.margins*2))

    def addInfo(self, label, info):
        self.updateInfo(label, info)
        self.target.setHeight(self.target.height()+15)

    def updateInfo(self, label, info):
        self.info_panels[label] = info
        self.max_width = 0
        for k in self.info_panels:
            ww = self.fm.width("%s: %s"%(k, self.info_panels[k]))
            if ww > self.max_width:
                self.max_width = ww
        self.target.setWidth(self.max_width+self.margins*2)

    def clearInfo(self):
        self.target.setHeight(self.margins*2)
        self.info_panels = OrderedDict()

    def draw(self, QPainter):
        QPainter.fillRect(self.target, QColor(0, 0, 0, 200))
        QPainter.setPen(Qt.white)

        QPainter.setFont(self.font)
        for i, k in enumerate(self.info_panels):
            QPainter.drawText(int(self.target.left()+self.margins), int(self.target.top()+self.margins+12+15*i), "%s: %s"%(k, self.info_panels[k]))

