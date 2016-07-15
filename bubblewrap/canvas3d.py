# Created by: Jacob Lewis

# used to convert a 3d point to a 2d point
from cpps.dcel import IndexedDCEL
import cpps.dcel as dcel
import cpps.triangulations as triangulations
import math
from math import sin, cos
import numpy as np

EPS = 1.0e-8

class VisualDCELException(Exception):
    pass

class VisualDCEL(IndexedDCEL):
    CYLINDER = 0
    TORUS = 1
    GENUS2 = 2
    def __init__(self, type, w, h, *__args):
        """
        (type, width, height, __args: stop)
        """
        data = ()

        if isinstance(type, int):
            if type == self.CYLINDER:
                data = build_cylinder(Point3D(), w, h)
            elif type == self.TORUS:
                data = build_torus(Point3D(), w, h, __args[0] if len(__args) > 0 else None)
            elif type == self.GENUS2:
                data = build_genus2(Point3D(), w, h)
            else:
                raise VisualDCELException(str("Invalid DCEL type"))

        self.points = data[0]
        self.edges = data[1]
        self.e1 = data[3]
        self.e2 = data[4] if len(data) > 4 else None

        super().__init__(data[2])


class Point3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.s_point = np.array((x, y, z))  # original location
        self.s_point.shape = (3, 1)
        self.point = np.array((x, y, z))  # transformed location
        self.point.shape = (3, 1)

    def update(self, x, y, z):
        self.point = np.array((x, y, z))  # transformed location
        self.point.shape = (3, 1)

    def place(self, x, y, z):
        self.s_point = np.array((x, y, z))  # original location
        self.s_point.shape = (3, 1)
        self.point = np.array((x, y, z))  # transformed location
        self.point.shape = (3, 1)

    def copy(self):
        return Point3D(self.x, self.y, self.z)

    @property
    def x(self):
        return self.point[0]

    @property
    def y(self):
        return self.point[1]

    @property
    def z(self):
        return self.point[2]

    @property
    def sx(self):
        return self.s_point[0]

    @property
    def sy(self):
        return self.s_point[1]

    @property
    def sz(self):
        return self.s_point[2]

    def __idiv__(self, other):
        self.point /= other

    def __add__(self, other):
        return Point3D(self.point[0] + other.point[0],
                       self.point[1] + other.point[1],
                       self.point[2] + other.point[2])

    def __iadd__(self, other):
        self.point += other.point

    def __str__(self):
        return "x: %f, y: %f, z: %f" % (self.point[0], self.point[1], self.point[2])

def translate_3d_points(points3d, translate_point3d):
    for point3d in points3d:
        point3d += translate_point3d


def rotate_3d_points(points3d, rotate_point3d, around_point3d, orient=False):
    """
    Relative rotation (will rotate with respect to current orientation)
    :param points3d: the points to rotate (in list form)
    :param rotate_point3d: a Point3D object containing the rotation in 3-axis as x,y,z
    :param around_point3d: a Point3D object containing the point at which to rotate around
    :return:
    """
    c = around_point3d

    for point in points3d:
        poi = np.array((point.x - c.x, point.y - c.y, point.z - c.z))
        poi.shape = (3, 1)
        __spin__(point, rotate_point3d, c, poi, orient)


def orient_3d_points(points3d, rotate_point3d, around_point3d):
    """
    Absolute rotation (will rotate with respect to original orientation)
    :param points3d: the points to rotate (in list form)
    :param rotate_point3d: a Point3D object containing the rotation in 3-axis as x,y,z
    :param around_point3d: a Point3D object containing the point at which to rotate around
    :return:
    """
    c = around_point3d

    for point in points3d:
        poi = np.array((point.sx - c.x, point.sy - c.y, point.sz - c.z))
        poi.shape = (3, 1)
        __spin__(point, rotate_point3d, c, poi)


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
    p1 = Point3D()
    for point in points3d:
        p1 = p1 + point
    p1.__idiv__(len(points3d))
    return p1


class Point2D:
    def __init__(self, x=0.0, y=0.0):
        self.point = [x, y]

    @property
    def x(self):
        return self.point[0]

    @property
    def y(self):
        return self.point[1]

    def __idiv__(self, other):
        self.point[0] /= other
        self.point[1] /= other

    def __add__(self, other):
        return Point2D(self.point[0] + other.point[0],
                       self.point[1] + other.point[1])

    def __iadd__(self, other):
        self.point[0] += other.point[0]
        self.point[1] += other.point[1]

    def __str__(self):
        return "x: %f, y: %f" % tuple(self.point)


def get_2d_point(point3d):
    factor = 0.9985
    return Point2D(point3d.x * factor ** point3d.z, point3d.y * factor ** point3d.z)


def get_2d_points(points3d):
    return [get_2d_point(point3d) for point3d in points3d]


class Line3D:

    def __init__(self, point3d_a, point3d_b):
        self.a = point3d_a
        self.b = point3d_b


def build_ring(center3D, num_of_points, radius):
    # There must be at least 3 points to create a ring.  Otherwise, the ring is a line or a point
    assert num_of_points > 2
    c = center3D
    n = num_of_points
    r = radius
    step = 2 * math.pi / n

    points = []
    edges = []

    for i in range(n):
        x = c.x + math.cos(step*i) * r
        y = c.y + math.sin(step*i) * r
        z = c.z  # no depth
        points.append(Point3D(x, y, z))
        if i > 0:
            edges.append(Line3D(points[i-1], points[i]))

    # connect last line
    edges.append(Line3D(points[-1], points[0]))

    return points, edges


def build_cylinder(base_center3D, w, h):
    assert w > 2 and h > 0
    c = base_center3D
    n1 = w
    n2 = h
    r = w/2
    step = 2

    points = []
    edges = []

    for i in range(n2):
        p, e = build_ring(c + Point3D(0, 0, step * i), n1, r)
        points += p
        edges += e
        # attach rings
        if i > 0:
            for k in range(w):
                edges.append(Line3D(points[(i-1)*w+k], points[i*w+k]))
                if k == w-1:
                    edges.append(Line3D(points[(i - 1) * w + k], points[i * w]))
                if k != 0:
                    edges.append(Line3D(points[(i-1)*w+k-1], points[i*w+k]))

    # build dcel
    mD, t1, b1 = triangulations.cylinder(w, h)

    # return:
    # graphics (points, edges)
    # DCEL (mD, t1: top starting edge, b1: bottom starting edge)
    return points, edges, mD, t1, b1


def build_torus(center3D, w, h, stop=None):
    assert w > 2 and h > 0
    c = center3D
    n1 = w
    n2 = h
    r = w/2
    tr = 10*n2 / (2*math.pi)
    step = 2 * math.pi / n2

    points = []
    edges = []

    for i in range(h):
        p, e = build_ring(c + Point3D(tr, 0, 0), n1, r)
        rotate_3d_points(p, Point3D(0, step*i, 0), c, orient=True)

        points += p
        edges += e
        # attach rings
        if i > 0:
            for k in range(w):
                edges.append(Line3D(points[(i-1)*w+k],points[i*w+k]))
                if k == w-1:
                    edges.append(Line3D(points[(i - 1) * w + k], points[i * w]))
                if k != 0:
                    edges.append(Line3D(points[(i-1)*w+k-1], points[i*w+k]))

                if i == h-1:
                    edges.append(Line3D(points[i * w + k], points[k]))

                    if k == w - 1:
                        edges.append(Line3D(points[i * w + k], points[0]))
                    if k != 0:
                        edges.append(Line3D(points[i * w + k - 1], points[k]))

    # Build dcel
    mD, t1, b1 = triangulations.cylinder(w, h)

    if stop is None:
        dcel.glue_boundary(mD, t1, b1)
    else:
        t1stop = t1.boundary_forward(stop)
        dcel.glue_boundary(mD,t1,b1,t1stop)

    # return:
    # graphics (points, edges)
    # DCEL (mD, t1: starting edge)
    return points, edges, mD, t1

def build_genus2(center3D, w, h):
    # TODO: not complete, this is just two tori tangent to each other

    tr = h / (2*math.pi)

    points = []
    edges = []

    p, e, mD1, t1 = build_torus(center3D+Point3D(tr+w, 0, 0), w, h, stop=1)
    points += p
    edges += e

    p, e, mD2, t2 = build_torus(center3D+Point3D(-tr-w, 0, 0), w, h, stop=1)
    points += p
    edges += e

    # dcel.reverse_orientation(mD2)
    # mD = mD1 | mD2
    # dcel.glue_boundary(mD,t1stop,t2stop)

    return points, edges

if __name__=="__main__":
    p1 = Point3D()
    p2 = Point3D(x=1)
    p3 = Point3D(y=1)
    p4 = Point3D(z=1)
    p5 = Point3D(x=1, z=1)
    p6 = Point3D(x=1, y=1)
    p7 = Point3D(y=1, z=1)
    p8 = Point3D(x=1, y=1, z=1)

    print(get_2d_points((p1,p2,p3,p4,p5,p6,p7,p8)))
