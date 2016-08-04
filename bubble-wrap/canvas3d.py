# Created by: Jacob Lewis

import math
import numpy as np
import dcel

from math import sin, cos
from cocycles import EmbeddedDCEL
from embeddings import embedded_torus, embedded_cylinder

EPS = 1.0e-8

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


if __name__ == "__main__":
    p1 = CoordinateVertex()
