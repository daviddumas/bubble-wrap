import circle
import mobius
import numpy as np


c0 = circle.from_center_radius(5+8j, 7)

c1 = circle.from_center_radius(0+0j, 1)

p1 = 1
p2 = 2
p3 = 3

q1 = 2
q2 = 9
q3 = 7

"""

T(z) = az + b
       cz + d

"""
a = np.linalg.det(np.array(((p1 * q1, q1, 1), (p2 * q2, q2, 1), (p3 * q3, q3, 1))))

b = np.linalg.det(np.array(((p1 * q1, p1, q1),
                           (p2 * q2, p2, q2),
                           (p3 * q3, p3, q3))))

c = np.linalg.det(np.array(((p1, q1, 1),
                           (p2, q2, 1),
                           (p3, q3, 1))))

d = np.linalg.det(np.array(((p1 * q1, p1, 1),
                           (p2 * q2, p2, 1),
                           (p3 * q3, p3, 1))))

def T(z):
    return (a*z + b)/(c*z + d)

print(T(p1), T(p2), T(p3))
