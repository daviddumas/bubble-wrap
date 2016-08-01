"""
A simple PyQt5 Import UI example

Created by: Jacob Lewis
Date: June 8th, 2016
"""

import sys

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

V_NUM = "0.1"


class scene(QGraphicsScene):
    def __init__(self, parent=None):

        super(QGraphicsScene, self).__init__(parent)




class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        uic.loadUi('ui/widget.ui', self)


        self.gvs = self.gv

        scene = QGraphicsScene()

        self.gvs.setSceneRect(0,0,self.gvs.width()-2,self.gvs.height()-2)
        self.gvs.setScene(scene)

        scene.addEllipse(10,10,100,100,QPen(Qt.red), QBrush(Qt.SolidPattern))
        #




        btn1 = self.testbtn1
        btn1.clicked.connect(lambda: scene.clear())
        btn2 = self.testbtn2
        btn2.clicked.connect(lambda: scene.addEllipse(20, 20, 200, 200, QPen(Qt.red), QBrush(Qt.SolidPattern)))
        btn3 = self.testbtn3
        btn3.clicked.connect(lambda: print("btn3"))


        self.setWindowTitle('CPPS UI From XML Example v%s' % V_NUM)

    def resizeEvent(self, QResizeEvent):
        print("width %d, height %d" % (self.width(), self.height()))
        self.gvs.setSceneRect(0,0,self.gvs.width()-2,self.gvs.height()-2)


if __name__ == '__main__':
    # This is the minimum needed to show the Window
    app = QApplication(sys.argv)
    w = Form()
    w.show()
    sys.exit(app.exec_())
