"""
main.py
"""

import sys

from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import gzip
import numpy as np

import cpps.serialization as ser
import cpps.dcel as dcel
import cpps.cocycles as cocycles
import cpps.mobius as mobius
import cpps.circle as circle
from calculation_view import ControlCalculations
from graphics_view import ControlGraphics
from canvas3d import Point3D

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

        """
        ACTIONS
        """
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
        self.mainWidget.circles = []
        # Old circles
        # self.circles = [c.from_center_radius(0 + 0j, 50), c.from_center_radius(100 + 0j, 50),
        #                   c.from_center_radius(-100 + 0j, 50), c.from_center_radius(0+100j, 50),
        #                   c.from_center_radius(0 - 100j, 50)]

        # Connect Controllers
        self.mainWidget.graphics = ControlGraphics(self.mainWidget)
        self.mainWidget.calculations = ControlCalculations(self.mainWidget)

        # EXTRA
        import numpy as np
        a = np.array((1, 2, 3))
        print(np.linalg.norm(a))

    def openNew(self):

        file = QFileDialog.getOpenFileName()
        if file[0] == None or len(file[0])<5:
            return
        print(len(file[0]))
        print("Open a new file: %s" % str(file[0]))



        ww = QDialog(self)
        ww.exec_()

        meta, D, chains, P = ser.zloadfn(file[0], cls=cocycles.InterstitialDCEL)


        def commutator(a, b):
            return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))

        def conjugate(inner, outer):
            return mobius.sl2inv(outer).dot(inner).dot(outer)

        recip = np.array([[0, 1j], [1j, 0]])


        print('Computing circle positions...')

        echains = dcel.edge_chain_dfs(D, chains['t1'][0])
        vchains = set()
        vert_seen = set()
        for ch in echains:
            if ch[-1].src not in vert_seen:
                vert_seen.add(ch[-1].src)
                vchains.add(ch)
        c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"
        dev_chains = set()  # Will store (chain,holonomy word) pairs for general pictures later
        for ch in vchains:
            h = D.hol(ch, P['750.0'])
            c = c0.transform_gl2(h)
            if not c.contains_infinity and c.radius > .005:
                dev_chains.add(ch)

        def show_fund(DD, edge_chains, X):
            rho0 = {k: DD.hol(edge_chains[k], X) for k in ['a1', 'a2', 'b1', 'b2']}
            rho = {'a1': rho0['a1'],
                   'b1': rho0['b1'],
                   'a2': conjugate(rho0['a2'], rho0['b2']),
                   'b2': rho0['b2']}
            fc = mobius.fix(commutator(rho['a1'], rho['b1']))
            fa1 = mobius.fix(rho['a1'])
            fa2 = mobius.fix(rho['a2'])
            mnorm = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
            mnorm = recip.dot(mnorm)
            output_circles = []
            for ch in dev_chains:
                h = DD.hol(ch, X)
                c = c0.transform_gl2(h).transform_sl2(mnorm)
                if c.radius > .005:
                    output_circles.append(c)
                    print('Generated %d circles' % len(output_circles))
                    self.mainWidget.circles = output_circles

        show_fund(D, chains, P['750.0'])
        # for c in self.mainWidget.circles:
        #     c.transform_sl2(((0.0001,0),
        #                      (0,1)))
        self.mainWidget.graphics.draw()

    def resizeEvent(self, QResizeEvent):
        print("width %d, height %d" % (self.width(), self.height()))


if __name__ == '__main__':
    # This is the minimum needed to show the Window
    app = QApplication(sys.argv)
    w = Form()
    w.show()
    sys.exit(app.exec_())
