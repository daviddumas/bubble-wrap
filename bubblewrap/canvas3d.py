# Created by: Jacob Lewis

# used to convert a 3d point to a 2d point

from cpps.dcel import IndexedDCEL
import cpps.dcel as dcel
import math
from math import sin, cos
import numpy as np
from embeddings import embedded_torus, embedded_cylinder

EPS = 1.0e-8

class VisualDCELException(Exception):
    pass

class EmbeddedDCEL(IndexedDCEL):
    # CYLINDER = 0
    # TORUS = 1
    # GENUS2 = 2
    def __init__(self, data):

        self.e1 = data[1]
        self.e2 = data[2] if len(data) > 2 else None

        super().__init__(data[0])
    pass


#>>>Generators<<<


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

#>>>Functions to create embedded DCELS<<<


def circular_torus_of_revolution(nw, nh, rmaj, rmin, vcenter=None):
    _torus_coord_gen = lambda i, j: circ_torus_param(rmaj, rmin, float(i) / nw, float(j) / nh)
    return EmbeddedDCEL(data=embedded_torus(nw, nh, coord_gen=_torus_coord_gen))


def cylinder_of_revolution(nw, nh, rad, height, vcenter=None):
    _torus_coord_gen = lambda i, j: circ_cylinder_param(height, rad, float(i) / nw, float(j) / nh)
    return EmbeddedDCEL(data=embedded_cylinder(nw, nh, coord_gen=_torus_coord_gen))

#>>>END FUNCTIONS<<<


class CoordinateVertex(dcel.Vertex):
    def __init__(self, coords=(0, 0, 0), leaving=None):
        self.static_coords = np.array(coords)  # original location
        self.static_coords.shape = (3, 1)
        self.coordinates = np.array(coords)  # transformed location
        self.coordinates.shape = (3, 1)

        super(CoordinateVertex, self).__init__(leaving)

    def update(self, x, y, z):
        self.coordinates = np.array((x, y, z))  # transformed location
        self.coordinates.shape = (3, 1)

    def place(self, x, y, z):
        self.static_coords = np.array((x, y, z))  # original location
        self.static_coords.shape = (3, 1)
        self.coordinates = np.array((x, y, z))  # transformed location
        self.coordinates.shape = (3, 1)

    def copy(self):
        return CoordinateVertex(self.coordinates, leaving=self.leaving)

    @property
    def x(self):
        return self.coordinates[0]

    @property
    def y(self):
        return self.coordinates[1]

    @property
    def z(self):
        return self.coordinates[2]

    @property
    def sx(self):
        return self.static_coords[0]

    @property
    def sy(self):
        return self.static_coords[1]

    @property
    def sz(self):
        return self.static_coords[2]
    #
    # def __idiv__(self, other):
    #     self.point /= other
    #

    def __add__(self, other):
        return CoordinateVertex((self.x + other.x, self.y + other.y, self.z + other.z))

    def __iadd__(self, other):
        self.coordinates += other.coordinates

    def __str__(self):
        return "x: %f, y: %f, z: %f" % (self.coordinates[0], self.coordinates[1], self.coordinates[2])


def translate_coordinates(coords, translate_coord):
    for point3d in coords:
        point3d += translate_coord


def rotate_coordinates(coords, rotate_coord, around_coord=CoordinateVertex(), orient=False):
    """
    Relative rotation (will rotate with respect to current orientation)
    :param coords: the points to rotate (in list form)
    :param rotate_coord: a Point3D object containing the rotation in 3-axis as x,y,z
    :param around_coord: a Point3D object containing the point at which to rotate around
    :return:
    """
    c = around_coord

    for point in coords:
        poi = np.array((point.x - c.x, point.y - c.y, point.z - c.z))
        poi.shape = (3, 1)
        __spin__(point, rotate_coord, c, poi, orient)


def orient_coordinates(coords, rotate_coord, around_coord=CoordinateVertex()):
    """
    Absolute rotation (will rotate with respect to original orientation)
    :param coords: the points to rotate (in list form)
    :param rotate_coord: a Point3D object containing the rotation in 3-axis as x,y,z
    :param around_coord: a Point3D object containing the point at which to rotate around
    :return:
    """
    c = around_coord

    for point in coords:
        poi = np.array((point.sx - c.x, point.sy - c.y, point.sz - c.z))
        poi.shape = (3, 1)
        __spin__(point, rotate_coord, c, poi)


def __spin__(p, rotate_point3d, c, poi, orient=False):
    # rotation matrix
    # (for more info on how it works: https://en.wikipedia.org/wiki/Rotation_matrix)
    r1 = rotate_point3d.x
    r2 = rotate_point3d.y
    r3 = rotate_point3d.z

    # Rotation Matrix
    xyz_r = np.array(((cos(r3)*cos(r2), -sin(r3)*cos(r1)+sin(r1)*sin(r2)*cos(r3),   sin(r1)*sin(r3)+cos(r1)*sin(r2)*cos(r3)),
                    (cos(r2)*sin(r3),   cos(r1)*cos(r3)+sin(r1)*sin(r2)*sin(r3),    -sin(r1)*cos(r3)+cos(r1)*sin(r2)*sin(r3)),
                    (-sin(r2),          sin(r1)*cos(r2),                            cos(r1)*cos(r2))))
    fin = xyz_r.dot(poi)

    fin[np.abs(fin) < EPS] = 0

    if orient:
        p.place(c.x + fin[0], c.y + fin[1], c.z + fin[2])
    else:
        p.update(c.x + fin[0], c.y + fin[1], c.z + fin[2])


def get_3d_center(points3d):
    p1 = CoordinateVertex()
    for point in points3d:
        p1 = p1 + point
    p1.__idiv__(len(points3d))
    return p1


class Point2D:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y

    def __str__(self):
        return "x: %f, y: %f" % (self.x, self.y)


def get_2d_point(point3d):
    factor = 0.9985
    return Point2D(point3d.x * factor ** point3d.z, point3d.y * factor ** point3d.z)


def get_2d_points(points3d):
    return [get_2d_point(point3d) for point3d in points3d]


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
