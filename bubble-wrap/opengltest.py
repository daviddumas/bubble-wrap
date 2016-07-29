# Installation command:
# pip3 install PyOpenGL PyOpenGL_accelerate

from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from widgets import *
import PyQt5.QtCore as QtCore
from math import *
import numpy as np

from canvas3d import circular_torus_of_revolution

class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.widget = glWidget(self)
        self.widget.setContentsMargins(0, 0, 0, 0)

        mainLayout = QFormLayout()
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.addWidget(self.widget)

        self.setLayout(mainLayout)

    def resizeEvent(self, QResizeEvent):
        pass
        # self.widget.setMinimumWidth(self.width())
        # self.widget.setMinimumHeight(self.height())


def matrix_rotate(r1, r2, r3, x, y, z):
    # Rotation Matrix
    xyz_r = np.array(((cos(r3) * cos(r2), -sin(r3) * cos(r1) + sin(r1) * sin(r2) * cos(r3),
                       sin(r1) * sin(r3) + cos(r1) * sin(r2) * cos(r3)),
                      (cos(r2) * sin(r3), cos(r1) * cos(r3) + sin(r1) * sin(r2) * sin(r3),
                       -sin(r1) * cos(r3) + cos(r1) * sin(r2) * sin(r3)),
                      (-sin(r2), sin(r1) * cos(r2), cos(r1) * cos(r2))))
    poi = np.array((x, y, z))
    poi.shape = (3, 1)
    res = xyz_r.dot(poi)
    # remove small numbers
    res[abs(res) < 1e-10] = 0
    print(res)
    return res[0][0], res[1][0], res[2][0]


class glWidget(QGLWidget):


    def __init__(self, parent):
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(640, 480)
        self.mouse_pos = [-1e5, -1e5, -1e5, -1e5]
        self.rX = 0
        self.rY = 0
        self.rZ = 0
        self.diff = (0, 0, 0)

        self.btn = 0

        self.zoom = 45
        self.m_dcel = circular_torus_of_revolution(10, 10, rmaj=1, rmin=0.5)


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
        if self.btn == QtCore.Qt.LeftButton:
            self.rX = self.diff[0] + self.mouse_pos[3] - self.mouse_pos[1]
            self.rY = self.diff[1] + self.mouse_pos[2] - self.mouse_pos[0]
        elif self.btn == QtCore.Qt.RightButton:
            self.rZ = self.diff[2] + self.mouse_pos[2] - self.mouse_pos[0] - self.mouse_pos[3] + self.mouse_pos[1]

        self.repaint()

    def mouseReleaseEvent(self, mouse):
        self.diff = (self.rX, self.rY, self.rZ)
        matrix_rotate(self.rX*pi/180, self.rY*pi/180, self.rZ*pi/180, 1, 1, 0)
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



if __name__ == '__main__':
    app = QApplication(['Yo'])
    window = MainWindow()
    window.show()
    app.exec_()