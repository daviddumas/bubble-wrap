"""Circle objects supporting linear fractional transformations"""

# Based on circles.c from lim by Curtis McMullen

import numpy as np
from .mobius import sl2inv

_LINE_EPS = 1e-8

class Circle:
    def __init__(self,m):
        """Circle in CP^1 represented by its inversion anti-mobius map"""
        self.m = np.array(m,dtype='complex')
        assert self.m.shape == (2,2)

    @property
    def contains_infinity(self):
        return abs(np.imag(self.m[1,0])) < _LINE_EPS

    @property
    def center(self):
        return self.m[0,0] / self.m[1,0]

    @property
    def radius(self):
        return 1.0 / np.imag(self.m[1,0])

    @property
    def line_base(self):
        return 0.5 * self.m[0,0] * self.m[0,1]

    @property
    def line_angle(self):
        return np.angle(self.m[0,0])

    def transform_gl2(self,T):
        T = np.array(T,dtype='complex')
        T = T / np.sqrt(np.linalg.det(T))
        return self.transform_sl2(T)

    def transform_sl2(self,T):
        T = np.array(T,dtype='complex')
        TI = sl2inv(T)
        return Circle(T.dot(self.m.dot(np.conj(TI))))

    def __str__(self):
        if self.contains_infinity:
            return 'Line(c={}, arg={}*pi)'.format(self.line_base,self.line_angle/np.pi)
        else:
            return 'Circle(c={}, r={})'.format(self.center,self.radius)

    def __repr__(self):
        s = np.array_str(self.m)
        s = s.replace('\n',' ')
        if self.contains_infinity:
            return 'Line(m={}; c={}, arg={}*pi)'.format(s,self.line_base,self.line_angle/np.pi)
        else:
            return 'Circle(m={}; c={}, r={})'.format(s,self.center,self.radius)


def from_center_radius(center,radius):
    c = center
    r = radius
    return Circle( [[1j*c/r, 1j*(r - (np.abs(c)**2)/r)],
                    [1j*(1/r), 1j*(-np.conj(c)/r)]] )


def from_point_angle(point,theta):
    p = point
    u = np.exp(1j*theta)
    return Circle( [[u, (np.conj(u)*p - u*np.conj(p))],
                    [0, np.conj(u) ]] )


def steiner_chain_xratio(n):
    return 2.0*np.cos(np.pi/n)
