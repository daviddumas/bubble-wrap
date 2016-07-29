# Created by: Jacob Lewis

# used to convert a 3d point to a 2d point
import math
from math import sin, cos

import dcel
import numpy as np
from OpenGL.GL import *

from cocycles import InterstitialDCEL
from embeddings import embedded_torus, embedded_cylinder

EPS = 1.0e-8

class VisualDCELException(Exception):
    pass

class EmbeddedDCEL(InterstitialDCEL):
    """
    V: set of vertices
    E: set of Edges
    F: set of Faces
    e1: starting edge 1
    e2: starting edge 2, if applicable
    """
    def __init__(self, data):
        self.e1 = data[1]
        self.e2 = data[2] if len(data) > 2 else None

        super().__init__(data[0])

    def paintGL(self):
        glBegin(GL_TRIANGLES)
        for face in self.F:
            e0 = face.edge
            glVertex3f(e0.src.coordinates[0], e0.src.coordinates[1], e0.src.coordinates[2])
            e_n = e0.next
            while e_n is not e0:
                glVertex3f(e_n.src.coordinates[0], e_n.src.coordinates[1], e_n.src.coordinates[2])
                e_n = e_n.next
        glEnd()


# >>> Coordinate Generators <<<


def circ_cylinder_param(h, r, i, j):
    ang = 2*math.pi*i
    x, z = r*math.cos(ang), r*math.sin(ang)
    y = h*j
    return CoordinateVertex(coords=(x, y, z))


def circ_torus_param(rmaj, rmin, i, j):
    ang_maj = 2 * math.pi * i
    ang_min = 2 * math.pi * j

    x, z = (rmaj + rmin * math.cos(ang_maj))*cos(ang_min), (rmaj + rmin * math.cos(ang_maj))*sin(ang_min)
    y = rmin * sin(ang_maj)

    return CoordinateVertex(coords=(x, y, z))

# >>> Functions to create embedded DCELS <<<


def circular_torus_of_revolution(nw, nh, rmaj, rmin, vcenter=None):
    _torus_coord_gen = lambda i, j: circ_torus_param(rmaj, rmin, float(i) / nw, float(j) / nh)
    return EmbeddedDCEL(data=embedded_torus(nw, nh, coord_gen=_torus_coord_gen))


def cylinder_of_revolution(nw, nh, rad, height, vcenter=None):
    _torus_coord_gen = lambda i, j: circ_cylinder_param(height, rad, float(i) / nw, float(j) / nh)
    return EmbeddedDCEL(data=embedded_cylinder(nw, nh, coord_gen=_torus_coord_gen))

# >>> Extra <<<


class CoordinateVertex(dcel.Vertex):
    def __init__(self, coords=(0, 0, 0), leaving=None):
        self.coordinates = np.array(coords)  # transformed location
        self.coordinates.shape = (3, 1)

        super(CoordinateVertex, self).__init__(leaving)



# def build_cylinder(base_center3D, w, h):
#     assert w > 2 and h > 0
#     c = base_center3D
#     n1 = w
#     n2 = h
#     r = w/2
#     step = 2
#
#     points = []
#     edges = []
#
#     for i in range(n2):
#         p, e = build_ring(c + Point3D(0, 0, step * i), n1, r)
#         points += p
#         edges += e
#         # attach rings
#         if i > 0:
#             for k in range(w):
#                 edges.append(Line3D(points[(i-1)*w+k], points[i*w+k]))
#                 if k == w-1:
#                     edges.append(Line3D(points[(i - 1) * w + k], points[i * w]))
#                 if k != 0:
#                     edges.append(Line3D(points[(i-1)*w+k-1], points[i*w+k]))
#
#     # build dcel
#     mD, t1, b1 = triangulations.cylinder(w, h)
#
#     # return:
#     # graphics (points, edges)
#     # DCEL (mD, t1: top starting edge, b1: bottom starting edge)
#     return points, edges, mD, t1, b1


def build_genus2(center3D, w, h):
    # TODO: not complete, this is just two tori tangent to each other
    pass
    # tr = h / (2*math.pi)
    #
    # points = []
    # edges = []
    #
    # p, e, mD1, t1 = build_torus(center3D+CoordinateVertex(tr+w, 0, 0), w, h, stop=1)
    # points += p
    # edges += e
    #
    # p, e, mD2, t2 = build_torus(center3D+CoordinateVertex(-tr-w, 0, 0), w, h, stop=1)
    # points += p
    # edges += e
    #
    # # dcel.reverse_orientation(mD2)
    # # mD = mD1 | mD2
    # # dcel.glue_boundary(mD,t1stop,t2stop)
    #
    # return points, edges

if __name__=="__main__":
    p1 = CoordinateVertex()
