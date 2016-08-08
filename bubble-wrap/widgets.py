import math

from collections import OrderedDict
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import assets
                       
class BaseWidget:
    def __init__(self, image_src=None, source=None, target=None, image2_src=None):
        """
        This class is the base widget which controls the basic button functionality
        :param image_src: main img
        :param source: image dimensions
        :param target: drawing dimensions
        :param image2_src: pressed img
        """
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
    NO_HIT = 0
    RIGHT = 1
    UP = 2
    LEFT = 3
    DOWN = 4

    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['dpad_norm'], QRectF(0,0,52,52), targetQRect)
        self.current_act = self.NO_HIT

    def draw(self, QPainter):
        # decide which image to paint to screen
        if self.current_act==self.NO_HIT:
            super().draw(QPainter)
        elif(self.current_act==self.RIGHT):
            QPainter.drawImage(self.target, QImage(assets.image['dpad_right.png']), self.source)
        elif(self.current_act==self.UP):
            QPainter.drawImage(self.target, QImage(assets.image['dpad_up']), self.source)
        elif(self.current_act==self.LEFT):
            QPainter.drawImage(self.target, QImage(assets.image['dpad_left']), self.source)
        elif(self.current_act==self.DOWN):
            QPainter.drawImage(self.target, QImage(assets.image['dpad_down']), self.source)

    def isHit(self, mouse):
        if super().isHit(mouse):
            a45 = 0.785398
            a90 = 1.570796
            angle = math.atan2(self.center[1]-mouse.pos().y(), mouse.pos().x()-self.center[0])
            if a45 > angle >= -a45:
                self.current_act = self.RIGHT
                return self.RIGHT
            elif a45+a90 > angle >= a45:
                self.current_act = self.UP
                return self.UP
            elif a45+a90 <= angle or -a45-a90 >= angle:
                self.current_act = self.LEFT
                return self.LEFT
            else:
                self.current_act = self.DOWN
                return self.DOWN
        else:
            self.current_act = 0
            return False

    def release(self):
        self.current_act = 0

class CenterWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['center_norm'], QRectF(0,0,22,22), targetQRect, image2_src=assets.image['center_act'])

class MobiusResetWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['mobius_reset_norm'], QRectF(0,0,22,22), targetQRect, image2_src=assets.image['mobius_reset_act'])

class PlusWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['plus_norm'], QRectF(0,0,22,22), targetQRect, image2_src=assets.image['plus_act'])

class MinusWidget(BaseWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['minus_norm'], QRectF(0,0,22,22), targetQRect, image2_src=assets.image['minus_act'])

class ToggleWidget(BaseWidget):
    def __init__(self, image_src=None, source=None, target=None, image2_src=None):
        super().__init__(image_src, source, target, image2_src)
        self.active = False

    def isActive(self, mouse):
        if super().isHit(mouse):
            self.active = not self.active

        self.hit = self.active
        return self.active

class MobiusToggleWidget(ToggleWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['mobius_norm'], QRectF(0,0,32,32), targetQRect, image2_src=assets.image['mobius_act'])

class DualGraphToggleWidget(ToggleWidget):
    def __init__(self, targetQRect=QRectF(0,0,0,0)):
        super().__init__(assets.image['dual_graph_norm'], QRectF(0,0,22,22), targetQRect, image2_src=assets.image['dual_graph_act'])

class InfoWidget(BaseWidget):
    def __init__(self):
        """
        This widget displays information within a transparent black box
        """
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

