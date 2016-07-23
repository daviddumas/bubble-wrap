# Installation command:
# pip3 install PyOpenGL PyOpenGL_accelerate

from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from widgets import *
from math import sqrt, sin, cos
from canvas3d import get_2d_points, EmbeddedDCEL, circular_torus_of_revolution, cylinder_of_revolution


class glWidget(QGLWidget):

    def __init__(self, delegate):
        QGLWidget.__init__(self, None)
        self.mouse_pos = [-1e5, -1e5, -1e5, -1e5]
        self.rX = 0
        self.rY = 0
        self.rZ = 0
        self.diff = (0, 0, 0)

        self.btn = 0

        self.zoom = 45
        self.m_dcel = delegate.m_dcel

    def paintGL(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glTranslatef(0, 0, -6)
        glRotate(self.rX, 1, 0, 0)
        glRotate(self.rY, 0, 1, 0)
        glRotate(self.rZ, 0, 0, 1)
        glColor3f(1.0, 0.0, 0.0)
        glPolygonMode(GL_FRONT, GL_LINE)
        #glPolygonMode(GL_FRONT, GL_FILL)
        glPolygonMode(GL_BACK, GL_LINE)

        glBegin(GL_TRIANGLES)
        for face in self.m_dcel.F:
            e0 = face.edge
            glVertex3f(e0.src.coordinates[0], e0.src.coordinates[1], e0.src.coordinates[2])
            e_n = e0.next
            while e_n is not e0:
                glVertex3f(e_n.src.coordinates[0], e_n.src.coordinates[1], e_n.src.coordinates[2])
                e_n = e_n.next

        glEnd()

        # posx, posy = 0, 0
        # sides = 32
        # radius = 1.5
        # glColor3f(0.1, 0.1, 0.1)
        # glPolygonMode(GL_FRONT, GL_FILL)
        # glPolygonMode(GL_BACK, GL_FILL)
        # glBegin(GL_POLYGON)
        # for i in range(sides):
        #     cosine = radius * cos(i * 2 * pi / sides) + posx
        #     sine = radius * sin(i * 2 * pi / sides) + posy
        #     glVertex2f(cosine, sine)
        #
        # glEnd()

        glFlush()

    def wheelEvent(self, event):
        wheel_point = event.angleDelta()/60
        self.zoom += wheel_point.y()
        print(self.zoom)
        self.fix_size()
        self.repaint()

    def mousePressEvent(self, mouse):
        self.mouse_pos[0:1] = mouse.pos().x(),mouse.pos().y()
        self.btn = mouse.button()

    def mouseMoveEvent(self, mouse):
        self.mouse_pos[2:3] = mouse.pos().x(), mouse.pos().y()

        print(mouse.button())
        if self.btn == Qt.LeftButton:
            self.rX = self.diff[0] + self.mouse_pos[3] - self.mouse_pos[1]
            self.rY = self.diff[1] + self.mouse_pos[2] - self.mouse_pos[0]
        elif self.btn == Qt.RightButton:
            self.rZ = self.diff[2] + self.mouse_pos[2] - self.mouse_pos[0] - self.mouse_pos[3] + self.mouse_pos[1]

        self.repaint()

    def mouseReleaseEvent(self, mouse):
        self.diff = (self.rX, self.rY, self.rZ)
        self.mouse_pos = self.mouse_pos = [-1e5, -1e5, -1e5, -1e5]

    def initializeGL(self):

        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        glClearColor(0.9, 0.9, 0.9, 1.0)

        self.fix_size()

    def resizeGL(self, p_int, p_int_1):
        self.fix_size()

    def fix_size(self):
        # fixes aspect and size of viewport when viewport is resized
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = self.width() / self.height()
        gluPerspective(self.zoom, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

class MyScene(QWidget):
    def __init__(self, delegate, parent=None):
        super().__init__(parent)
        self.delegate = delegate

        self.dpad = TranslateWidget()
        self.izoom = PlusWidget()
        self.ozoom = MinusWidget()
        self.infoPanel = InfoWidget()
        self.infoPanel.addInfo("Valences", "(work in progress)")

        self.mp = -1e10, -1e10

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
        qp.drawEllipse(self.center[0] + self.mp[0] - 1,
                       self.center[1] + self.mp[1] - 1,
                       2, 2)


        print("cursor:", self.mp)
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
            red_dist = [1e10, None, None]
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

                        ax, ay, bx, by, mx, my = self.center[0] + 200 * cir.center.real, self.center[1] + 200 * cir.center.imag, \
                                                 self.center[0] + 200 * cir2.center.real, self.center[1] + 200 * cir2.center.imag, self.mp[0]+self.center[0], self.mp[1]+self.center[1]

                        bias = 10
                        qp.setPen(Qt.black)
                        if (ax+bias > mx > bx-bias or ax-bias < mx < bx+bias) and (ay+bias > my > by-bias or ay-bias < my < by+bias):
                            d1 = ax - bx, ay - by
                            d2 = ax - mx, ay - my
                            a1 = math.atan2(d1[1], d1[0])
                            a2 = math.atan2(d2[1], d2[0])
                            da = abs(a1-a2)
                            dist = math.sin(da) * sqrt(d2[0]**2 + d2[1]**2)
                            if dist < bias and dist < red_dist[0]:
                                if red_dist[1] is not None:
                                    rax, ray, rbx, rby = self.center[0] + 200 * red_dist[1].center.real, self.center[1] + 200 * red_dist[1].center.imag, \
                                                             self.center[0] + 200 * red_dist[2].center.real, self.center[1] + 200 * red_dist[2].center.imag
                                    qp.drawLine(rax, ray, rbx, rby)
                                red_dist = [dist, cir, cir2]
                                qp.setPen(Qt.red)

                        qp.drawLine(ax, ay, bx, by)
                if v in v_drawn:
                    continue
                v_drawn.append(v)

                if not cir.contains_infinity:
                    #add ellipses to an array for optimization
                    if v.valence > 6:
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

        self.infoPanel.setPos(0, self.height-self.infoPanel.height)
        self.infoPanel.draw(qp)

        print("drawn!")
        qp.end()

    def mouseReleaseEvent(self, QMouseEvent):
        self.izoom.release()
        self.ozoom.release()
        self.dpad.release()
        self.delegate.graphics.draw()

    def mousePressEvent(self, mouse):
        d = self.delegate

        self.mp = mouse.pos().x()-self.center[0], mouse.pos().y()-self.center[1]

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
        d.graphics.draw()




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
        self.delegate.m_dcel = circular_torus_of_revolution(10, 10, rmaj=1, rmin=0.5)
        #self.delegate.m_dcel = cylinder_of_revolution(10, 10, vcenter=None, rad=15, height=40)

        self.delegate.opengl = glWidget(self.delegate)
        self.delegate.opengl.setContentsMargins(0,0,0,0)
        self.delegate.scene2 = MyScene(self.delegate)
        self.delegate.scene2.setContentsMargins(0, 0, 0, 0)

        self.delegate.gv2.addWidget(self.delegate.scene2)
        self.delegate.gv1.addWidget(self.delegate.opengl)

    def draw(self, view=-1):
        if view == -1 or view == 0:
            self.delegate.opengl.update()

        if view == -1 or view == 1:
            self.delegate.scene2.update()