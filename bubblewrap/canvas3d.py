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
                data = cylinder(w, h, Vertex3D())
            elif type == self.TORUS:
                data = build_torus(Vertex3D(), w, h, __args[0] if len(__args) > 0 else None)
            elif type == self.GENUS2:
                data = build_genus2(Vertex3D(), w, h)
            else:
                raise VisualDCELException(str("Invalid DCEL type"))
        self.e1 = data[1]
        self.e2 = data[2] if len(data) > 2 else None

        super().__init__(data[0])




class Vertex3D(dcel.Vertex):
    def __init__(self, x=0.0, y=0.0, z=0.0, leaving=None):
        self.s_point = np.array((x, y, z))  # original location
        self.s_point.shape = (3, 1)
        self.point = np.array((x, y, z))  # transformed location
        self.point.shape = (3, 1)

        super(Vertex3D, self).__init__(leaving)

    def update(self, x, y, z):
        self.point = np.array((x, y, z))  # transformed location
        self.point.shape = (3, 1)

    def place(self, x, y, z):
        self.s_point = np.array((x, y, z))  # original location
        self.s_point.shape = (3, 1)
        self.point = np.array((x, y, z))  # transformed location
        self.point.shape = (3, 1)

    def copy(self):
        return Vertex3D(self.x, self.y, self.z, leaving=self.leaving)

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
        return Vertex3D(self.point[0] + other.point[0],
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
    p1 = Vertex3D()
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


def ring(w, center3D=Vertex3D(), dh=None):
    """Generate DCEL for a triangulated ring of height 1 and circumference w.

    Looks like:.. --T----------------...
                  |\  |\  |\  |\  |\
                \ | \ | \ | \ | \ | \
                 \|  \|  \|  \|  \|  \
                ..--B-----------------...
    Returns typle (D,T,B)
    D -- DCEL of the ring
    T -- a "top" half-edge
    B -- a "bottom" half edge directly below T
    """

    # We create the vertices first in a 2d array; later the indices
    # will correspond to position in the ring as follows:
    #
    # 00---01---02---03---04---05
    # |\   |\   |\   |\   |\   |
    # | \  | \  | \  | \  | \  |
    # |  \ |  \ |  \ |  \ |  \ |
    # |   \|   \|   \|   \|   \|
    # 10---11---12---13---14---15

    # TODO: Are we able to somehow reference the other method that was written?  Maybe add a `v` param to allow
    # vertices to be added
    V = [__build_ring3D(center3D, w), # start at center
         __build_ring3D(center3D+Vertex3D(0, 0, (w/2) if dh is None else dh), w)] # move back second ring

    # EVERYTHING ELSE IS THE SAME, ONLY MODIFICATION IS ABOVE. ^^^
    E = set()
    F = set()

    # Top triangles
    for i in range(w):
        j = (i + 1) % w
        EF, f = dcel.vertex_chain_to_face([V[1][j], V[0][j], V[0][i]])
        if i == 0:
            for e in EF:
                if e.src == V[0][1] and e.dst == V[0][0]:
                    etop = e
                    break
        E.update(EF)
        F.add(f)

    # Bottom triangles
    for i in range(w):
        j = (i + 1) % w
        EF, f = dcel.vertex_chain_to_face([V[0][i], V[1][i], V[1][j]])
        if i == 0:
            for e in EF:
                if e.src == V[1][0] and e.dst == V[1][1]:
                    ebot = e
                    break
        E.update(EF)
        F.add(f)

    # TODO: inefficient to search blindly for twin pairs, when we know
    # exactly which ones are present.  Make this more efficient.
    # (Since vertex_chain_to_face doesn't expose any details about the
    # order of edges returned, it is probably best to just manually
    # create all of half-edges and store in an array like V.
    dcel.set_twins(E)

    # ADDED RETURN OF VERTICES
    return dcel.DCEL(V[0] + V[1], E, F), etop, ebot, V

def cylinder(w,h, center3D=Vertex3D(), dh=None):
    # dh: (delta height)
    """Generate DCEL for a triangulated cylinder of height h and circumference w"""
    tops = []
    bottoms = []
    D = dcel.DCEL()

    vertex_list = []

    # Create h separate rings of height 1
    for i in range(h):
        RD,t,b,v_list = ring(w, center3D + Vertex3D(z=(w/2 if dh is None else dh)*i), dh)
        vertex_list.append(v_list)
        tops.append(t)
        bottoms.append(b)
        D |= RD

    # Glue the rings top-to-bottom
    for i in range(h-1):
        dcel.glue_boundary(D, bottoms[i], tops[i+1])

    return D, tops[0], bottoms[-1], vertex_list

def __build_ring3D(center3D, w):
    # There must be at least 3 points to create a ring.  Otherwise, the ring is either a line or a point
    assert w > 2
    c = center3D
    n = w
    r = w/2
    step = 2 * math.pi / n

    points = []

    for i in range(n):
        x = c.x + math.cos(step*i) * r
        y = c.y + math.sin(step*i) * r
        z = c.z  # no depth
        points.append(Vertex3D(x, y, z))

    return points


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


def build_torus(center3D, w, h, stop=None):
    assert w > 2 and h > 2
    tr = 10*h / (2*math.pi)
    step = 2 * math.pi / h

    # Build dcel
    mD, t1, b1, v_list = cylinder(w, h, center3D+Vertex3D(x=tr), dh=0)

    print("item is list: ", len(v_list))
    for i, v in enumerate(v_list):
        rotate_3d_points(v[1], Vertex3D(y=i*step), Vertex3D(), orient=True)
        print([str(v) for v in v[1]])

    if stop is None:
        dcel.glue_boundary(mD, b1, t1)
    else:
        t1stop = t1.boundary_forward(stop)
        dcel.glue_boundary(mD,t1,b1,t1stop)

    # return:
    # DCEL (mD, t1: starting edge)
    return mD, t1

def build_genus2(center3D, w, h):
    # TODO: not complete, this is just two tori tangent to each other

    tr = h / (2*math.pi)

    points = []
    edges = []

    p, e, mD1, t1 = build_torus(center3D+Vertex3D(tr+w, 0, 0), w, h, stop=1)
    points += p
    edges += e

    p, e, mD2, t2 = build_torus(center3D+Vertex3D(-tr-w, 0, 0), w, h, stop=1)
    points += p
    edges += e

    # dcel.reverse_orientation(mD2)
    # mD = mD1 | mD2
    # dcel.glue_boundary(mD,t1stop,t2stop)

    return points, edges

if __name__=="__main__":
    p1 = Vertex3D()
    p2 = Vertex3D(x=1)
    p3 = Vertex3D(y=1)
    p4 = Vertex3D(z=1)
    p5 = Vertex3D(x=1, z=1)
    p6 = Vertex3D(x=1, y=1)
    p7 = Vertex3D(y=1, z=1)
    p8 = Vertex3D(x=1, y=1, z=1)

    print(get_2d_points((p1,p2,p3,p4,p5,p6,p7,p8)))
