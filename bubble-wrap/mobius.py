"""Utility functions related to mobius transformations"""

import numpy as np

def sl2inv(m):
    return np.array( [[ m[1,1], -m[0,1] ],
                      [ -m[1,0], m[0,0] ]] )

def make_sl2(m):
    return np.array(m)/np.sqrt(np.linalg.det(m))

def chi(z1,z2,z3,z4):
    return (z1-z3)*(z2-z4)/((z1-z4)*(z2-z3))

def center_four_points(pa,pb,qa,qb):
    w = chi(pa,pb,qa,qb)
    z = (2 + 2*np.sqrt(1 - w) - w)/w
    if abs(z) < 1.0:
        z = 1/z
    a = -pa + qa - (pa - 2*pb + qa)*z
    b = -pb*qa*(1 + z) + pa*(pb - pb*z + 2*qa*z)
    c = 2*pb + qa*(-1 + z) - pa*(1 + z)
    d = pa*(2*qa + pb*(-1 + z)) - pb*qa*(1 + z)
    return make_sl2([[a,b],[c,d]])

def fix(m):
    a = m[0,0]
    b = m[0,1]
    c = m[1,0]
    d = m[1,1]
    disc = 4*b*c + (a-d)**2
    return ((a-d) - np.sqrt(disc))/(2*c), ((a-d) + np.sqrt(disc))/(2*c)

def center_two_hyperbolics(A,B,configuration='X'):
    fa = fix(A)
    fb = fix(B)
    if configuration=='X':
        return center_four_points(fa[0],fb[0],fa[1],fb[1])
    elif configuration=='II':
        return center_four_points(fa[0],fa[1],fb[0],fb[1])
    else:
        raise ValueError('Unknown configuraiton "%s"; known types are "X" and "II".' % configuration)

def sl2_rho(m):
    """Spectral radius of element of SL(2,C)"""
    t = np.trace(m)
    d = np.sqrt(t*t - 4.0)
    rho = abs(0.5*(t+d))
    if rho < 1.0:
        rho = 1 / rho
    return rho

def three_point_sl2(p1, p2, p3, q1, q2, q3):
    """Transformation from p1 -> q1, p2 -> q2, p3 -> q3"""
    a = np.linalg.det(np.array(((p1 * q1, q1, 1),
                                (p2 * q2, q2, 1),
                                (p3 * q3, q3, 1))))

    b = np.linalg.det(np.array(((p1 * q1, p1, q1),
                                (p2 * q2, p2, q2),
                                (p3 * q3, p3, q3))))

    c = np.linalg.det(np.array(((p1, q1, 1),
                                (p2, q2, 1),
                                (p3, q3, 1))))

    d = np.linalg.det(np.array(((p1 * q1, p1, 1),
                                (p2 * q2, p2, 1),
                                (p3 * q3, p3, 1))))

    return make_sl2([[a, b], [c, d]])


def transform_point(T, p):
    return (T[0][0]*p + T[0][1]) / (T[1][0]*p + T[1][1])