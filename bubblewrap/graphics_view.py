from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from widgets import *
import cpps.triangulations as triangulations
from math import sqrt, sin, cos
from canvas3d import Vertex3D, get_2d_points, translate_3d_points, Line3D, rotate_3d_points, VisualDCEL


class MyScene(QWidget):
    def __init__(self, delegate, parent=None):
        super().__init__(parent)
        self.delegate = delegate

        self.dpad = TranslateWidget()
        self.izoom = PlusWidget()
        self.ozoom = MinusWidget()

    @property
    def width(self):
        return self.frameSize().width()

    @property
    def height(self):
        return self.frameSize().height()

    @property
    def center(self):
        return self.width / 2, self.height / 2

    def paintEvent(self, QPaintEvent):
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.fillRect(QRect(0, 0, self.width, self.height), QColor(250, 250, 250, 255))
        qp.setPen(Qt.black)
        #qp.setBrush(Qt.black)

        d = self.delegate

        # if d.testRad is not None:
        #     qp.drawEllipse(self.center[0],
        #                    self.center[1] - d.testRad[0],
        #                    d.testRad[0] * 2,
        #                    d.testRad[0] * 2)

        # d.scene.clear()
        # draw circles

        if d.currentView == 1:
            scale = 10
            for p in get_2d_points(d.m_dcel.V):
                qp.drawEllipse(self.center[0] + scale*p.x-2,
                               self.center[1] + scale*p.y-2,
                               4, 4)
            for lns in d.m_dcel.E:
                ps = get_2d_points([lns.src, lns.next.src])
                qp.drawLine(self.center[0] + scale*ps[0].x, self.center[1] + scale*ps[0].y, self.center[0] + scale*ps[1].x, self.center[1] + scale*ps[1].y)
        else:
            v_to_c = {}
            for c, v in d.circles:
                v_to_c[v] = c

            edges_to_draw = []
            for cirs in d.circles:
                try:
                    edges_to_draw += list(cirs[1].star())
                except(Exception):
                    pass

            #print(edges_to_draw)
            v_drawn = []
            e_drawn = []
            print("drawing")
            for edg in edges_to_draw:
                v = edg.src
                v2 = edg.next.src

                cir = v_to_c[v]
                if v2 in v_to_c:
                    cir2 = v_to_c[v2]
                else:
                    cir2 = None

                if d.dual_graph and cir2 is not None and not cir.contains_infinity and edg.twin not in e_drawn:
                    e_drawn.append(edg)
                    if (cir.center.real - cir2.center.real)**2 + (cir.center.imag - cir2.center.imag)**2 <= (cir.radius + cir2.radius + 0.01) ** 2:
                        qp.drawLine(self.center[0] + 200 * (cir.center.real), self.center[1] + 200 * (cir.center.imag),
                                    self.center[0] + 200 * (cir2.center.real), self.center[1] + 200 * (cir2.center.imag))
                if v in v_drawn:
                    continue
                v_drawn.append(v)

                if not cir.contains_infinity:
                    #add ellipses to an array for optimization
                    if abs(cir.radius)>0.3:
                        qp.setPen(Qt.magenta)
                    elif abs(cir.radius)>0.2:
                        qp.setPen(Qt.darkBlue)
                    elif abs(cir.radius)>0.1:
                        qp.setPen(Qt.darkGreen)
                    elif abs(cir.radius)>0.05:
                        qp.setPen(Qt.red)
                    else:
                        qp.setPen(Qt.black)

                    qp.drawEllipse(self.center[0] + 200*(cir.center.real-cir.radius),
                                   self.center[1] + 200*(cir.center.imag-cir.radius),
                                   200 * (cir.radius*2), 200*(cir.radius*2))
                else:
                    # creates a straight line
                    x = self.center[0] + cir.line_base.real
                    y = self.center[1] + cir.line_base.imag
                    size = sqrt(cir.line_base.real**2 + cir.line_base.imag**2)
                    scrSizeAvg = (self.width+self.height)/2
                    size = scrSizeAvg if size < scrSizeAvg else size  # Makes sure the line will be long enough to fill the screen
                    # Draw the line out from the line_base in either direction
                    qp.drawLine(x - size*cos(cir.line_angle), y - size*sin(cir.line_angle), x + size*cos(cir.line_angle), y + size*sin(cir.line_angle))
                    print(cir.line_base, cir.line_angle)


        self.dpad.setPos(self.width-70, 20)
        self.dpad.draw(qp)
        self.izoom.setPos(self.width-55, 80)
        self.izoom.draw(qp)
        self.ozoom.setPos(self.width-55, 105)
        self.ozoom.draw(qp)

        print("drawn!")
        qp.end()

    def mouseReleaseEvent(self, QMouseEvent):
        self.izoom.release()
        self.ozoom.release()
        self.dpad.release()
        self.delegate.graphics.draw()

    def mousePressEvent(self, mouse):
        d = self.delegate

        T = None
        if self.izoom.isHit(mouse):
            # zoom in
            T = ((1.6, 0),
                 (0, 0.625))
        elif self.ozoom.isHit(mouse):
            # zoom out
            T = ((0.625, 0),
                 (0, 1.6))

        trans = self.dpad.isHit(mouse)

        if trans == 1:
            T = ((1, 0.5),
                 (0, 1))
        elif trans == 2:
            T = ((1, -0.5j),
                 (0, 1))
        elif trans == 3:
            T = ((1, -0.5),
                 (0, 1))
        elif trans == 4:
            T = ((1, 0.5j),
                 (0, 1))

        if T is not None:
            d.calculations.animate_all(T)




def drawHouse(d):
    p1 = Vertex3D()  #
    p2 = Vertex3D(x=50)  #
    p3 = Vertex3D(y=50)  #
    p4 = Vertex3D(z=50)
    p5 = Vertex3D(x=50, z=50)
    p6 = Vertex3D(x=50, y=50)  #
    p7 = Vertex3D(y=50, z=50)
    p8 = Vertex3D(x=50, y=50, z=50)
    p9 = Vertex3D(x=25, y=25, z=-25)
    d.points = [p1, p2, p3, p4, p5, p6, p7, p8, p9]
    translate_3d_points(d.points, Vertex3D(x=-25, y=-25, z=0))
    rotate_3d_points(d.points, Vertex3D(), Vertex3D(0,0,-475))

    l1 = Line3D(p1, p2)
    l2 = Line3D(p1, p3)
    l3 = Line3D(p1, p4)
    l4 = Line3D(p8, p5)
    l5 = Line3D(p8, p6)
    l6 = Line3D(p8, p7)
    l7 = Line3D(p5, p2)
    l8 = Line3D(p5, p4)
    l9 = Line3D(p6, p3)
    l10 = Line3D(p6, p2)
    l11 = Line3D(p7, p3)
    l12 = Line3D(p7, p4)

    l13 = Line3D(p9, p1)
    l14 = Line3D(p9, p2)
    l15 = Line3D(p9, p3)
    l16 = Line3D(p9, p6)
    d.lines = [l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16]


class ControlGraphics:

    def __init__(self, delegate):
        self.delegate = delegate
        # gv = QVBoxLayout()
        # gv.addWidget()
        self.delegate.points = []
        self.delegate.lines = []
        self.delegate.testRad = [2]
        """
        Uncomment the following to draw:
        """
        #drawHouse(self.delegate)
        self.delegate.m_dcel = VisualDCEL(VisualDCEL.TORUS, w=8, h=8)

        #D, t, b = triangulations.cylinder(5, 5)

        #print(D)

        self.delegate.scene = MyScene(self.delegate)
        self.delegate.scene.setContentsMargins(0,0,0,0)
        self.delegate.gv.addWidget(self.delegate.scene)

    def draw(self):
        self.delegate.scene.update()