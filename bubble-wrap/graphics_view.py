# Installation command:
# pip3 install PyOpenGL PyOpenGL_accelerate

import platform

from OpenGL import GL
from OpenGL.GLU import gluPerspective
from PyQt5.QtWidgets import *
from PyQt5.QtOpenGL import *
from widgets import *
from math import sqrt, sin, cos
from canvas3d import circular_torus_of_revolution, cylinder_of_revolution
import numpy as np
import mobius
import tools

class glWidget(QGLWidget):

    def __init__(self, delegate):

        formats = QGLFormat.defaultFormat()
        formats.setSampleBuffers(True)
        formats.setSamples(8)
        QGLFormat.setDefaultFormat(formats)

        QGLWidget.__init__(self, None)
        self.mouse_pos = [-1e5, -1e5, -1e5, -1e5]
        self.rX = 45
        self.rY = 0
        self.rZ = 0
        self.diff = (45, 0, 0)

        self.btn = 0

        self.zoom = 45
        self.delegate = delegate

    def paintGL(self):

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glLoadIdentity()

        GL.glTranslatef(0, 0, -6)
        GL.glRotate(self.rX, 1, 0, 0)
        GL.glRotate(self.rY, 0, 1, 0)
        GL.glRotate(self.rZ, 0, 0, 1)

        GL.glColor4f(0.0, 0.0, 0.0, 0.2)

        GL.glPolygonMode(GL.GL_FRONT, GL.GL_FILL)
        GL.glPolygonMode(GL.GL_BACK, GL.GL_LINE)
        self.delegate.m_dcel.paintGL()

        GL.glColor4f(0.0, 0.0, 0.0, 1)

        GL.glPolygonMode(GL.GL_FRONT, GL.GL_LINE)
        self.delegate.m_dcel.paintGL()

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

        GL.glFlush()

    def wheelEvent(self, event):
        wheel_point = event.angleDelta()/60
        self.zoom += wheel_point.y()
        self.fix_size()
        self.repaint()

    def mousePressEvent(self, mouse):
        self.mouse_pos[0:1] = mouse.pos().x(),mouse.pos().y()
        self.btn = mouse.button()

    def mouseMoveEvent(self, mouse):
        self.mouse_pos[2:3] = mouse.pos().x(), mouse.pos().y()
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

        GL.glClearDepth(1.0)
        GL.glDepthFunc(GL.GL_LESS)
        #GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_MULTISAMPLE)
        GL.glShadeModel(GL.GL_SMOOTH)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glClearColor(0.9, 0.9, 0.9, 1.0)

        self.fix_size()

    def resizeGL(self, p_int, p_int_1):
        self.fix_size()

    def fix_size(self):
        side = min(self.width(), self.height())
        GL.glViewport((self.width() - side) // 2, (self.height() - side) // 2, side, side)

        # fixes aspect and size of viewport when viewport is resized
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        aspect = self.width() / self.height() if platform.system() == 'Darwin' else 1
        gluPerspective(self.zoom, aspect, 0.1, 100.0)
        try:
            GL.glMatrixMode(GL.GL_MODELVIEW)
        except(Exception):
            print("zoomed in too much!!")

class MyScene(QWidget):
    draw_trigger = pyqtSignal()

    def __init__(self, delegate, parent=None):
        super().__init__(parent)
        self.delegate = delegate



        self.optimize_thread = None

        # display_params (zoom, pos:[relative to center])
        self.display_params = {"zoom": 100, "pos": [0, 0], "start_pos": [0, 0], "center": [0, 0], "width": 0, "height": 0}

        self.dpad = TranslateWidget()
        self.dgraphtog = DualGraphToggleWidget()
        self.recenter = CenterWidget()
        self.izoom = PlusWidget()
        self.ozoom = MinusWidget()
        self.infoPanel = InfoWidget()
        self.infoPanel.addInfo("Valences", "(work in progress)")

        self.lT = None
        self.force_update = True

        # cached circle transformations
        self.m_circles = []

        self.mp = -1e10, -1e10

        self.draw_trigger.connect(self.update)

    def paintEvent(self, QPaintEvent):
        # update sizes
        self.display_params["center"] = self.center
        self.display_params["width"] = self.width
        self.display_params["height"] = self.height

        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing)

        qp.fillRect(QRect(0, 0, self.width, self.height), QColor(250, 250, 250, 255))

        d = self.delegate

        if d.progressValue[0] < 100:
            pen = QPen(Qt.blue)
            pen.setWidth(5)
            qp.setPen(pen)
            loadingRect = QRect(self.center[0] - 20, self.center[1] - 20, 40, 40)
            qp.drawArc(loadingRect, 90*16, -int(d.progressValue[0]*3.6*16))
            qp.setPen(Qt.black)

        zoom = self.display_params["zoom"]
        offset = self.display_params["pos"].copy()

        # Detect if circle packing optimization is needed
        sameT = False
        try:
            if self.lT != d.packing_trans:
                self.force_update = True
            else:
                sameT = True
        except(Exception):
            self.force_update = True

        if self.force_update:
            self.force_update = False
            # If so, optimize circles

            # cancel old thread
            if self.optimize_thread is not None and self.optimize_thread.isRunning():
                self.optimize_thread.cancel = True

            # begin new optimization thread
            self.optimize_thread = tools.OptimizeCirclesThread(self, d.circles, d.circles_optimize, d.packing_trans[0], self.display_params)
            self.optimize_thread.start(priority=QThread.LowPriority)

        # >>> ALL Circles beyond this point are optimized <<<

        # transform circles
        T = mobius.make_sl2(d.packing_trans[0])
        if not sameT or len(self.m_circles) != len(d.circles_optimize[0]):
            self.m_circles = []
            for ci in d.circles_optimize[0]:
                # print(ci[0])
                self.m_circles.append((ci[0].transform_sl2(T), ci[1], ci[2]))
            self.lT = d.packing_trans.copy()

        # print off valence info
        if d.opened_dcel is not None:
            self.infoPanel.clearInfo()
            valences = get_valence_dict(d.opened_dcel.V)
            for k in valences:
                self.infoPanel.addInfo("Valence %s" % k, "%s vertices" % valences[k])
            if len(valences) == 0:
                self.infoPanel.addInfo("Status", "no packing visible")

        for c in self.m_circles:
            cir = c[0]
            v = c[1]
            if not cir.contains_infinity and np.abs(zoom * cir.radius) > 1:
                # add ellipses to an array for optimization
                if v.valence > 6:
                    qp.setPen(Qt.red)
                else:
                    qp.setPen(Qt.black)

                qp.drawEllipse(self.center[0] + offset[0] + zoom * (cir.center.real - cir.radius),
                               self.center[1] + offset[1] + zoom * (cir.center.imag - cir.radius),
                               zoom * (cir.radius * 2), zoom * (cir.radius * 2))
            elif cir.contains_infinity:
                # creates a straight line
                x = self.center[0] + offset[0] + cir.line_base.real
                y = self.center[1] + offset[1] + cir.line_base.imag
                size = 3 * sqrt((offset[0] + cir.line_base.real) ** 2 + (offset[1] + cir.line_base.imag) ** 2)
                scrSizeAvg = (self.width + self.height) / 2
                size = scrSizeAvg if size < scrSizeAvg else size  # Makes sure the line will be long enough to fill the screen
                # Draw the line out from the line_base in either direction
                qp.drawLine(x - size * cos(cir.line_angle), y - size * sin(cir.line_angle),
                            x + size * cos(cir.line_angle), y + size * sin(cir.line_angle))
                print(x, y, ":", size)
                print(cir.line_base, cir.line_angle)

        # TODO: code for dual graph:
        # draw circles
        v_drawn = []
        e_drawn = []
        v_to_v_drawn = []
        red_dist = [1e10, None, None]
        if d.dual_graph:
            edges_to_draw, v_to_c = parse_circles(self.m_circles, d.opened_dcel)
            for edg in edges_to_draw:
                v = edg.src
                v2 = edg.next.src

                if v not in v_to_c:
                    continue
                cir = v_to_c[v]
                if v2 in v_to_c:
                    cir2 = v_to_c[v2]
                else:
                    cir2 = None

                if cir2 is not None and not cir.contains_infinity and (v, v2) not in v_to_v_drawn and (v2, v) not in v_to_v_drawn:
                    v_to_v_drawn.append((v, v2))
                    draw_dual_graph_seg(cir, cir2, zoom, offset, self.center, qp, self.mp)

        # Update widget positions and draw them
        self.dpad.setPos(self.width-70, 20)
        self.dpad.draw(qp)
        self.izoom.setPos(self.width-55, 80)
        self.izoom.draw(qp)
        self.ozoom.setPos(self.width-55, 105)
        self.ozoom.draw(qp)
        self.recenter.setPos(self.width-55, 130)
        self.recenter.draw(qp)
        self.dgraphtog.setPos(self.width-55, self.height-55)
        self.dgraphtog.draw(qp)

        self.infoPanel.setPos(0, self.height-self.infoPanel.height)
        self.infoPanel.draw(qp)

        qp.end()

    def mouseReleaseEvent(self, QMouseEvent):
        # release button presses
        self.izoom.release()
        self.ozoom.release()
        self.recenter.release()
        self.dpad.release()

        # force packing optimization and redraw
        self.force_update = True
        self.delegate.graphics.draw()

    def mousePressEvent(self, mouse):
        d = self.delegate
        pos_x = self.display_params["pos"][0]
        pos_y = self.display_params["pos"][1]
        zoom = self.display_params["zoom"]

        self.display_params["start_pos"] = [pos_x - mouse.pos().x(),
                                            pos_y - mouse.pos().y()]

        self.mp = mouse.pos().x()-self.center[0], mouse.pos().y()-self.center[1]

        if self.izoom.isHit(mouse):
            # zoom in
            # keeps circle packing centered when zooming
            self.delegate.calculations.animate_attributes(self.display_params,
                {"zoom":zoom * 1.5, "pos":[pos_x * 1.5, pos_y * 1.5]})
        elif self.ozoom.isHit(mouse):
            # zoom out
            # keeps circle packing centered when zooming
            self.delegate.calculations.animate_attributes(self.display_params,
                {"zoom": zoom / 1.5, "pos": [pos_x / 1.5, pos_y / 1.5]})
        elif self.recenter.isHit(mouse):
            # reset/recenter view
            self.delegate.calculations.animate_attributes(self.display_params, {"zoom": 100, "pos": [0, 0]})

        d.dual_graph = self.dgraphtog.isHit(mouse)

        # >>> Directional Pad (dpad) <<<
        # check for mouse interaction.  If there is a hit, trans will store the button pressed
        trans = self.dpad.isHit(mouse)
        # change attributes accordingly
        attr_changes = None
        if trans == TranslateWidget.RIGHT:
            attr_changes = {"pos": [pos_x - 20, pos_y]}
        elif trans == TranslateWidget.LEFT:
            attr_changes = {"pos": [pos_x + 20, pos_y]}
        elif trans == TranslateWidget.UP:
            attr_changes = {"pos": [pos_x, pos_y + 20]}
        elif trans == TranslateWidget.DOWN:
            attr_changes = {"pos": [pos_x, pos_y - 20]}
        if attr_changes is not None:
            self.delegate.calculations.animate_attributes(self.display_params, attr_changes)

        d.graphics.draw()

    def mouseMoveEvent(self, mouse):
        # move packing around with cursor
        self.display_params["pos"][0] = self.display_params["start_pos"][0] + mouse.pos().x()
        self.display_params["pos"][1] = self.display_params["start_pos"][1] + mouse.pos().y()
        self.update()

    def wheelEvent(self, event):
        # zoom in and out of the packing
        wheel_point = event.angleDelta()/60

        self.display_params["zoom"] *= 1.2**wheel_point.y()
        # keeps circle packing centered when zooming
        self.display_params["pos"][0] *= 1.2**wheel_point.y()
        self.display_params["pos"][1] *= 1.2**wheel_point.y()

        self.force_update = True
        self.update()

    @property
    def width(self):
        return self.frameSize().width()

    @property
    def height(self):
        return self.frameSize().height()

    @property
    def center(self):
        return self.width / 2, self.height / 2


def parse_circles(circles, D):
    """
    Used for Dual Graph (this may retire)
    :param circles:
    :param D:
    :return:
    """
    v_to_c = {}
    for c, v, d in circles:
        if d:
            v_to_c[v] = c

    return D.UE if D is not None else [], v_to_c

def draw_dual_graph_seg(cir, cir2, zoom, offset, center, qp, mp):
    # TODO: fix/finish
    if (cir.center.real - cir2.center.real) ** 2 + (cir.center.imag - cir2.center.imag) ** 2 <= (cir.radius + cir2.radius + 0.01) ** 2:

        ax, ay, bx, by, mx, my = center[0] + offset[0] + zoom * cir.center.real, center[1] + offset[1] + zoom * cir.center.imag, \
                                 center[0] + offset[0] + zoom * cir2.center.real, center[1] + offset[1] + zoom * cir2.center.imag, mp[0] + center[0], mp[1] + \
                                 center[1]

        # bias = 10
        qp.setPen(Qt.blue)
        # if (ax + bias > mx > bx - bias or ax - bias < mx < bx + bias) and (
        #                         ay + bias > my > by - bias or ay - bias < my < by + bias):
        #     d1 = ax - bx, ay - by
        #     d2 = ax - mx, ay - my
        #     a1 = math.atan2(d1[1], d1[0])
        #     a2 = math.atan2(d2[1], d2[0])
        #     da = abs(a1 - a2)
        #     dist = math.sin(da) * sqrt(d2[0] ** 2 + d2[1] ** 2)
        #     if dist < bias and dist < red_dist[0]:
        #         if red_dist[1] is not None:
        #             rax, ray, rbx, rby = self.center[0] + 200 * red_dist[1].center.real, self.center[
        #                 1] + 200 * red_dist[1].center.imag, \
        #                                  self.center[0] + 200 * red_dist[2].center.real, self.center[
        #                                      1] + 200 * red_dist[2].center.imag
        #             qp.drawLine(rax, ray, rbx, rby)
        #         red_dist = [dist, cir, cir2]
        #         qp.setPen(Qt.red)

        qp.drawLine(ax, ay, bx, by)

def get_valence_dict(verts):
    """
    Finds the valences of the vertices supplied
    :param verts:
    :return: a dict of valences with their count
    """
    from collections import defaultdict
    verts_of_valence = defaultdict(int)
    for v in verts:
        verts_of_valence[v.valence] += 1
    return dict(verts_of_valence)

class ControlGraphics:
    """
    Graphics controller attached to main delegate
    """

    def __init__(self, delegate):
        self.delegate = delegate

        # default shape displayed
        self.delegate.m_dcel = circular_torus_of_revolution(4, 4, rmaj=1, rmin=0.5)

        self.delegate.opengl = glWidget(self.delegate)
        self.delegate.opengl.setContentsMargins(0, 0, 0, 0)
        self.delegate.scene2 = MyScene(self.delegate)
        self.delegate.scene2.setContentsMargins(0, 0, 0, 0)

        self.delegate.gv2.addWidget(self.delegate.scene2)
        self.delegate.gv1.addWidget(self.delegate.opengl)

    def force_update(self):
        self.delegate.scene2.force_update = True

    def draw(self, view=-1):
        if view == -1 or view == 0:
            self.delegate.opengl.update()

        if view == -1 or view == 1:
            self.delegate.scene2.update()

