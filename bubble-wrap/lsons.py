"""Least Squares Overdetermined Newton Solver"""

# LSONS: a simple Least Squares Overdetermined Newton Solver
# Written in 2013 by David Dumas <david@dumas.io>

# To the extent possible under law, the author has dedicated all
# copyright and related and neighboring rights to this software to the
# public domain worldwide. This software is distributed without any
# warranty.

from __future__ import print_function

import numpy as np


class SolverException(Exception):
    pass

_DERIV_EPS = 1e-12

def numjac(f,X,epsilon=_DERIV_EPS):
    Y0 = f(X)
    J = np.zeros( (len(Y0),len(X)) )
    for i in range(len(X)):
        deltaX = np.zeros_like(X)
        deltaX[i] = epsilon
        Y1 = f(X + deltaX)
        Yprime = (Y1 - Y0) / epsilon
        J[:,i] = Yprime
    return J

def lsroot(fun, jac, x0, args=(), maxiter=500, relax=0.9, normgoal=0.0000001, maxcond=1e7,verbose=False,monitor=None):
    '''Least squares root finder for overdetermined systems.

    Takes:
        fun(x) : callable vector function (dim(f(x)) > dim(x)),
        jac(x) : jacobian of fun
        x0 : initial vector
        args : extra arguments for f and J, passed after x
        maxiter : Raise error if no root found within this many iterations
        normgoal : Consider a root if residual less than this float
        relax : Step by 0.9*(linearization root step)
        maxcond : Raise error if condition number of Jacobian exceeds this float

    Algorithm: Compute linear approximation L0 of fun at x0, solve the
       overdetermined linear system L0(x1) = 0 in the least squares
       sense to get x1, repeat, to get sequence xn.

       If this sequence eventually gives residual of norm less than normgoal, return.

       If maxiter reached, raise SolverException.
    '''
    n = 1
    x = x0
    while True:
        y = fun(x,*args)
        norm = np.linalg.norm(y)
        if norm < normgoal:
            break
        if monitor:
            monitor(x,y,norm)
        J = jac(x,*args)
        if verbose:
            if n == 1:
                print('N = %d  norm = %g' % (n,norm))
            else:
                print('N = %d  norm = %g  deltax=%g' % (n,norm,normdeltax))
        try:
            v, residual, rank, s = np.linalg.lstsq(J,y)
        except np.linalg.LinAlgError as e:
            raise SolverException(str(e))
        CN = max(s) / min(s)
        if CN > maxcond:
            raise SolverException('condition number exceeded maxcond (%g)' % maxcond)
        normdeltax = np.linalg.norm(relax*v)
        x = x - relax*v
        n = n + 1
        if (n > maxiter):
            raise SolverException('maxiter (%d) iterations without success' % maxiter)

    if verbose:
        print('Successs (norm < %g) after %d iterations' % (normgoal,n-1))
    return x

def main():
    import cmath
    
    def f(v):
        x,y = v
        r = (3+4j)*(cmath.exp(x-1) - 1.0) + x**3 * y**2 - 3*y * x**2 + 2*x * y**3 + 8*x*y - 8
        s = 2j*cmath.exp(2.0j * (1-y)) + x**2 * y**2 - 2j - 1
        return np.array([r+s,r*r+2j*s,r-s])

    def g(v):
        x,y = v
        r = (1-x)**2 + 100.0*(y - x**2)**2
        return np.array([r, 2*r, 3*r])

    def findif(f,z,epsilon=1e-10):
        return (f(z+epsilon) - f(z)) / epsilon

    J = lambda x:numjac(f,x)

    print(lsroot(f, lambda v:numjac(f,v), [0.2,0.3], verbose=True))

if __name__=='__main__':
    main()
