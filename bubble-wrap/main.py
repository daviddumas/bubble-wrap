#!/usr/bin/python3

__version__ = "0.2.5 (pre-alpha)"

import sys

import numpy as np
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import tools
from calculation_view import ControlCalculations
from canvas3d import circular_torus_of_revolution, cylinder_of_revolution
from graphics_view import ControlGraphics
from openpacking import openPacking

import assets

class Form(QMainWindow):
    draw_trigger = pyqtSignal()

    def __init__(self, parent=None):
        """
        Main Window for Bubble Wrap Application
        :param parent:
        """
        super(Form, self).__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.mainWidget = QWidget(parent)

        self.mainWidget.setWindowFlags(Qt.FramelessWindowHint)
        self.mainWidget.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(self.mainWidget)
        uic.loadUi(assets.ui['widget'], self.mainWidget)
        # Set the title/name of the frame
        self.setWindowTitle("Bubble Wrap {}".format(__version__))

        # >>> ACTIONS <<<
        self.setup_actions()

        # Bind all of the UI elements to be used later

        # Bind Data Structures
        self.mainWidget.uecp = tools.UnifiedEmbeddedCirclePacking()

        # Connect Controllers
        self.mainWidget.graphics = ControlGraphics(self.mainWidget)
        self.mainWidget.calculations = ControlCalculations(self.mainWidget)

        self.draw_trigger.connect(self.mainWidget.graphics.draw)

    def setup_actions(self):
        """
        Setup `File` actions
        """
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

        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)
        file_menu = menu_bar.addMenu('&File')

        file_menu.addAction(newAction)
        file_menu.addAction(openAction)
        file_menu.addAction(exitAction)

    # >>> Action Methods <<<

    def openNew(self):
        openPacking(self, self.mainWidget, lambda: self.mainWidget.graphics.draw())

    def createNew(self):
        uecp = self.mainWidget.uecp
        surfaces = ("Cylinder", "Torus", "Genus 2 Surface")
        surface_selected = tools.showDropdownDialog(self, surfaces, "Select a surface to create")
        print("Surface selected: %s" % surfaces[surface_selected])

        uecp.reset_data()

        # create the selected DCEL surface
        if surface_selected == 0:
            uecp.opened_dcel = cylinder_of_revolution(10, 10, rad=1, height=2)
        elif surface_selected == 1:
            uecp.opened_dcel = circular_torus_of_revolution(10, 10, rmaj=1, rmin=0.5)
        elif surface_selected == 2:
            print("Currently unable to create a Genus 2 surface yet.")

        self.mainWidget.graphics.draw()


if __name__ == '__main__':
    # This is the minimum needed to show the Window
    app = QApplication(sys.argv)
    w = Form()
    w.show()
    sys.exit(app.exec_())
