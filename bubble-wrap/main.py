"""
main.py
"""

__version__ = "0.15"

import sys

import numpy as np

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from calculation_view import ControlCalculations
from graphics_view import ControlGraphics
from openpacking import openPacking
from canvas3d import circular_torus_of_revolution, cylinder_of_revolution
import tools


class Form(QMainWindow):
    draw_trigger = pyqtSignal()

    @property
    def draw_trigger2(self):
        return self.draw_trigger

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setContentsMargins(0,0,0,0)
        self.mainWidget = QWidget(parent)

        self.mainWidget.setWindowFlags(Qt.FramelessWindowHint)
        self.mainWidget.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self.mainWidget)
        uic.loadUi('ui/widget.ui', self.mainWidget)
        # Set the title/name of the frame
        self.setWindowTitle('CPPS UI From XML Example v%s' % __version__)

        # >>> ACTIONS <<<
        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        openAction = QAction('&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open File')
        openAction.triggered.connect(self.openNew)

        newAction = QAction('&New', self)
        newAction.setShortcut('Ctrl+N')
        newAction.setStatusTip('Create a New Object')
        newAction.triggered.connect(self.createNew)

        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)
        fileMenu = menubar.addMenu('&File')

        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        # self.topFiller = QWidget(parent)
        # self.topFiller.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Bind all of the UI elements to be used later

        # Bind Data Structures
        self.mainWidget.m_dcel = None
        self.mainWidget.circles = []
        self.mainWidget.opened_dcel = None
        self.mainWidget.dual_graph = False
        self.mainWidget.packing_trans = [np.array(((1, 0), (0, 1)), dtype='complex')]

        # Connect Controllers
        self.mainWidget.graphics = ControlGraphics(self.mainWidget)
        self.mainWidget.calculations = ControlCalculations(self.mainWidget)

        self.draw_trigger.connect(self.mainWidget.graphics.draw)

    def openNew(self):
        openPacking(self, lambda: self.mainWidget.graphics.draw())

    def createNew(self):
        surfaces = ("Cylinder", "Torus", "Genus 2 Surface")
        surface_selected = tools.showDropdownDialog(self, surfaces, "Select a surface to create")
        print("Surface selected: %s" % surfaces[surface_selected])
        # create the selected DCEL surface
        if surface_selected == 0:
            self.mainWidget.m_dcel = cylinder_of_revolution(10, 10, rad=1, height=2)
        elif surface_selected == 1:
            self.mainWidget.m_dcel = circular_torus_of_revolution(10, 10, rmaj=1, rmin=0.5)

        elif surface_selected == 2:
            print("Currently unable to create a Genus 2 surface.")

        self.mainWidget.graphics.draw()


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


