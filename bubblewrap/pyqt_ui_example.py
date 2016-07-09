"""
A simple PyQt5 UI example

Created by: Jacob Lewis
Date: June 8th, 2016
"""

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import uic

import numpy as np
import cmath
from cmath import pi, e

V_NUM = "0.1"


class CircleCanvas(QGraphicsView):
    """
    Renders the circle
    """

    def __init__(self, circleCheckbox, parent=None):
        super(CircleCanvas, self).__init__(parent)
        self.circleCheckbox = circleCheckbox

    def paintEvent(self, QPaintEvent):
        qp = QPainter(self.viewport())

        qp.fillRect(QRect(0, 0, self.width(), self.height()), QColor(200, 200, 200, 255))
        qp.setPen(Qt.red)

        # only draw the circle if the circleCheckBox is checked
        if self.circleCheckbox.isChecked():
            qp.drawEllipse(10, 10, 200, 200)

        ctr = (self.width() // 2, self.height() // 2)

        # draw axises
        qp.drawLine(0, ctr[1], self.width(), ctr[1])
        qp.drawLine(ctr[0], 0, ctr[0], self.height())

        # Draw notches
        NOTCH_SEP = 30
        NOTCH_SIZE = 5
        for x in range(ctr[0] // NOTCH_SEP):
            dist = NOTCH_SEP * x
            qp.drawLine(ctr[0] + dist, ctr[1] - NOTCH_SIZE, ctr[0] + dist, ctr[1] + NOTCH_SIZE)
            qp.drawLine(ctr[0] - dist, ctr[1] - NOTCH_SIZE, ctr[0] - dist, ctr[1] + NOTCH_SIZE)
        for y in range(ctr[1] // NOTCH_SEP):
            dist = NOTCH_SEP * y
            qp.drawLine(ctr[0] - NOTCH_SIZE, ctr[1] + dist, ctr[0] + NOTCH_SIZE, ctr[1] + dist)
            qp.drawLine(ctr[0] - NOTCH_SIZE, ctr[1] - dist, ctr[0] + NOTCH_SIZE, ctr[1] - dist)

        #points = np.array([complex(x, y) for x in range(-50, 51) for y in range(50, -51, -1)])

        points = np.array([2, 0+2j, 0-2j, -2, 1.61803399, -0.618033989])

        qp.setPen(Qt.blue)
        self.display_points(qp, points, ctr, NOTCH_SEP)

        try:
            mTrans = (eval(self.a.toPlainText()), eval(self.b.toPlainText()),
                      eval(self.c.toPlainText()), eval(self.d.toPlainText()))

            for i in range(len(points)):
                # if points[i].real == points[i].imag == 0:
                #     continue
                points[i] = self.mob_trans(points[i], mTrans)

            points *= eval(self.a2.toPlainText())
            points += eval(self.b2.toPlainText())
        except Exception:
            pass

        # points[1] = self.mob_trans(points[1], mTrans)
        # points[2] = self.mob_trans(points[2], mTrans)
        # points[3] = self.mob_trans(points[3], mTrans)

        #points *= cmath.e**(1j*cmath.pi/4)

        print(points)
        # points[1] *= 1+1j
        # points[2] *= 1+1j
        # points[3] *= 1+1j

        qp.setPen(Qt.black)
        self.display_points(qp, points, ctr, NOTCH_SEP, 4)

        qp.end()

    def display_points(self, qp, points, ctr, sep_size, rad=2):
        for point in points:
            qp.drawEllipse(QRectF((ctr[0] + point.real * sep_size - rad),
                           (ctr[1] - point.imag * sep_size - rad),
                           rad*2,
                           rad*2))
    def mob_trans(self, z, trans):
        a, b, c, d = trans
        return (a * z + b) / (c * z + d)


class Form(QWidget):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)

        # The Dimensions of the side bar and bottom bar
        self.DIM_PANEL_RIGHT_WIDTH = 200
        self.DIM_PANEL_BOTTOM_HEIGHT = 50

        # Setup the basic window properties
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)

        # Setup the Panels
        self.setupSidePanel()
        self.setupBottomPanel()

        # Setup the Graphical View
        self.sceneLayout = QVBoxLayout()
        self.gview = CircleCanvas(self.showCircle)
        self.gview.a = self.a
        self.gview.b = self.b
        self.gview.c = self.c
        self.gview.d = self.d
        self.gview.a2 = self.a2
        self.gview.b2 = self.b2
        self.gview.setUpdatesEnabled(True)
        self.sceneLayout.addWidget(self.gview)

        # Setup and attach all views to the main grid
        self.grid = QGridLayout()
        self.grid.setColumnMinimumWidth(1, self.DIM_PANEL_RIGHT_WIDTH)
        self.grid.setRowMinimumHeight(1, self.DIM_PANEL_BOTTOM_HEIGHT)

        self.grid.addItem(self.sceneLayout, 0, 0)
        self.grid.addItem(self.bottomButtons, 1, 0)
        self.grid.addItem(self.groupHolder, 0, 1)

        # Set the layout the the grid
        self.setLayout(self.grid)
        self.setWindowTitle('CPPS Explorer v%s' % V_NUM)

    def setupSidePanel(self):
        # Side Panel
        self.groupHolder = QGridLayout()
        # Side Panel Group 1
        group1 = QVBoxLayout()
        titleLabel = QLabel("Mobius Transformation Params\n T(z) = (az+b)/(cz+d)")
        titleLabel.setMaximumHeight(30)
        self.a = QTextEdit("1")
        self.a.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH//2)
        self.a.setMaximumHeight(30)
        self.a.textChanged.connect(lambda: self.gview.viewport().repaint())
        self.b = QTextEdit("0")
        self.b.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH//2)
        self.b.setMaximumHeight(30)
        self.b.textChanged.connect(lambda: self.gview.viewport().repaint())
        self.c = QTextEdit("0")
        self.c.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH//2)
        self.c.setMaximumHeight(30)
        self.c.textChanged.connect(lambda: self.gview.viewport().repaint())
        self.d = QTextEdit("1")
        self.d.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH//2)
        self.d.setMaximumHeight(30)
        self.d.textChanged.connect(lambda: self.gview.viewport().repaint())

        sg1 = QVBoxLayout()
        sg1.setDirection(QBoxLayout.LeftToRight)
        sg1.addWidget(self.a)
        sg1.addWidget(self.b)

        sg2 = QVBoxLayout()
        sg2.setDirection(QBoxLayout.LeftToRight)
        sg2.addWidget(self.c)
        sg2.addWidget(self.d)

        slider1 = QSlider(Qt.Horizontal)
        slider1.setMinimum(-500)
        slider1.setMaximum(500)
        slider1.setValue(100)
        slider1.valueChanged.connect(lambda:self.a.setText(str(int(slider1.value())/100.0)))
        slider1.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH)

        slider2 = QSlider(Qt.Horizontal)
        slider2.setMinimum(-500)
        slider2.setMaximum(500)
        slider2.setValue(0)
        slider2.valueChanged.connect(lambda: self.b.setText(str(int(slider2.value()) / 100.0)))
        slider2.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH)

        slider3 = QSlider(Qt.Horizontal)
        slider3.setMinimum(-500)
        slider3.setMaximum(500)
        slider3.setValue(0)
        slider3.valueChanged.connect(lambda: self.c.setText(str(int(slider3.value()) / 100.0)))
        slider3.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH)

        slider4 = QSlider(Qt.Horizontal)
        slider4.setMinimum(-500)
        slider4.setMaximum(500)
        slider4.setValue(100)
        slider4.valueChanged.connect(lambda: self.d.setText(str(int(slider4.value()) / 100.0)))
        slider4.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH)

        group1.addWidget(titleLabel, alignment=Qt.AlignTop)
        group1.addWidget(slider1, alignment=Qt.AlignTop)
        group1.addWidget(slider2, alignment=Qt.AlignTop)
        group1.addWidget(slider3, alignment=Qt.AlignTop)
        group1.addWidget(slider4, alignment=Qt.AlignTop)
        group1.addItem(sg1)
        group1.addItem(sg2)

        #Side Panel Group 2
        group2 = QVBoxLayout()
        titleLabel2 = QLabel("Transform T(z) = (az+b)")

        # radio groups in group 2
        # radioGroup = QButtonGroup(group2)
        # radio1 = QRadioButton("Option 1")
        # radio1.toggled.connect(lambda: self.radioButtonChange(radio1))
        # radio1.setChecked(True)
        # radio2 = QRadioButton("Option 2")
        # radio2.toggled.connect(lambda: self.radioButtonChange(radio2))
        #
        # radioGroup.addButton(radio1)
        # radioGroup.addButton(radio2)
        #
        # radioGroup2 = QButtonGroup(group2)
        # radio3 = QRadioButton("Option 3a")
        # radio3.toggled.connect(lambda: self.radioButtonChange(radio3))
        # radio3.setChecked(True)
        # radio4 = QRadioButton("Option 2b")
        # radio4.toggled.connect(lambda: self.radioButtonChange(radio4))
        #
        # radioGroup2.addButton(radio3)
        # radioGroup2.addButton(radio4)

        self.a2 = QTextEdit("1")
        self.a2.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH // 2)
        self.a2.setMaximumHeight(30)
        self.a2.textChanged.connect(lambda: self.gview.viewport().repaint())
        self.b2 = QTextEdit("0")
        self.b2.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH // 2)
        self.b2.setMaximumHeight(30)
        self.b2.textChanged.connect(lambda: self.gview.viewport().repaint())

        sg3 = QVBoxLayout()
        sg3.setDirection(QBoxLayout.LeftToRight)
        sg3.addWidget(self.a2)
        sg3.addWidget(self.b2)

        slider5 = QSlider(Qt.Horizontal)
        slider5.setMinimum(-500)
        slider5.setMaximum(500)
        slider5.setValue(100)
        slider5.setMaximumHeight(30)
        slider5.valueChanged.connect(lambda: self.a2.setText(str(int(slider5.value()) / 100.0)))
        slider5.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH)

        slider6 = QSlider(Qt.Horizontal)
        slider6.setMinimum(-500)
        slider6.setMaximum(500)
        slider6.setValue(0)
        slider6.setMaximumHeight(30)
        slider6.valueChanged.connect(lambda: self.b2.setText(str(int(slider6.value()) / 100.0)))
        slider6.setMaximumWidth(self.DIM_PANEL_RIGHT_WIDTH)

        group2.addWidget(titleLabel2, alignment=Qt.AlignTop)
        group2.addWidget(slider5, alignment=Qt.AlignTop)
        group2.addWidget(slider6, alignment=Qt.AlignTop)
        group2.addItem(sg3)
        # group2.addWidget(radio1, alignment=Qt.AlignTop)
        # group2.addWidget(radio2, alignment=Qt.AlignTop)
        # group2.addWidget(radio3, alignment=Qt.AlignTop)
        # group2.addWidget(radio4, alignment=Qt.AlignTop)

        # attach all groups to group holder grid
        self.groupHolder.addItem(group1, 0, 0)  # group, row, col
        self.groupHolder.setRowMinimumHeight(1, 50)
        self.groupHolder.addItem(group2, 2, 0)  # group, row, col


    def setupBottomPanel(self):
        # Bottom Panel
        self.exitButton = QPushButton("Quit")
        self.exitButton.setMaximumWidth(100)
        self.exitButton.clicked.connect(self.exitNow)

        self.showCircle = QCheckBox("Draw Circle")
        self.showCircle.stateChanged.connect(self.checkboxChange)

        self.bottomButtons = QVBoxLayout()
        self.bottomButtons.setDirection(QBoxLayout.LeftToRight)
        #self.bottomButtons.addWidget(self.showCircle)
        self.bottomButtons.addWidget(self.exitButton)

    def radioButtonChange(self, radioBtn):
        if radioBtn.isChecked():
            print(radioBtn.text(), "is checked")

    def checkboxChange(self):
        # used to force a repaint to either display or hide the circle
        self.gview.viewport().repaint()
        print("checkbox is:", self.showCircle.isChecked())

    def exitNow(self):
        print("exit")
        exit()

    def resizeEvent(self, QResizeEvent):
        print("width %d, height %d" % (self.width(), self.height()))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = Form()
    w.show()
    sys.exit(app.exec_())
