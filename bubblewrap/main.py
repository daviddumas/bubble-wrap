"""
main.py
"""

import sys

import numpy as np

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from calculation_view import ControlCalculations
from graphics_view import ControlGraphics
from openpacking import openPacking

V_NUM = "0.1"



class Form(QMainWindow):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setContentsMargins(0,0,0,0)
        self.mainWidget = QWidget(parent)

        self.mainWidget.setWindowFlags(Qt.FramelessWindowHint)
        self.mainWidget.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self.mainWidget)
        uic.loadUi('ui/widget.ui', self.mainWidget)
        # Set the title/name of the frame
        self.setWindowTitle('CPPS UI From XML Example v%s' % V_NUM)

        # >>> ACTIONS <<<
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        openAction = QAction('&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open File')
        openAction.triggered.connect(self.openNew)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')

        fileMenu.addAction(exitAction)
        fileMenu.addAction(openAction)

        # self.topFiller = QWidget(parent)
        # self.topFiller.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Bind all of the UI elements to be used later

        # Bind Data Structures
        self.mainWidget.m_dcel = None
        self.mainWidget.circles = []
        self.mainWidget.circle_packing = []
        self.mainWidget.dual_graph = False
        self.mainWidget.packing_trans = [np.array(((1, 0), (0, 1)), dtype='complex')]

        # Connect Controllers
        self.mainWidget.graphics = ControlGraphics(self.mainWidget)
        self.mainWidget.calculations = ControlCalculations(self.mainWidget)

    def openNew(self):
        openPacking(self, lambda: self.mainWidget.graphics.draw())


    def resizeEvent(self, QResizeEvent):
        print("width %d, height %d" % (self.width(), self.height()))


if __name__ == '__main__':
    s_point = np.array((1, 2, 3))  # original location
    s_point.shape = (3, 1)
    print(s_point)

    # This is the minimum needed to show the Window
    app = QApplication(sys.argv)
    w = Form()
    w.show()
    sys.exit(app.exec_())


