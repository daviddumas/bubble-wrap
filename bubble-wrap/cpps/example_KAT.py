"""Find and describe Kobe Andreev Thurston circle packing for mirrored one holed torus"""

from collections import defaultdict

import cpps.circle as circle
import cpps.cocycles as cocycles
import cpps.dcel as dcel
import cpps.triangulations as triangulations
import numpy as np

import lsons as lsons

np.set_printoptions(suppress=True)

D,t,b = triangulations.cylinder(5, 5)
t2 = t.boundary_forward(2)
dcel.glue_boundary(D, t, b, t2)

chain_down = [t]
while True:
    e = chain_down[-1]
    a = e.tri_cw
    b = a.vert_ccw
    c = b.vert_ccw
    chain_down += [a,b,c]
    if c == t:
        break        

chain_right = [t]
while True:
    e = chain_right[-1]
    a = e.vert_ccw
    b = a.vert_ccw
    c = b.tri_cw
    chain_right += [a,b,c]
    if c == t:
        break

print('verts',len(D.V))
print('hedges',len(D.E))
print('faces',len(D.F))

topo = dcel.oriented_manifold_type(D)
for k in topo:
    print(k,topo[k])

verts_of_valence = defaultdict(int)
for v in D.V:
    verts_of_valence[v.valence] += 1
for k in verts_of_valence:
    print(verts_of_valence[k],'vertices of valence',k)

# Freeze and index the DCEL
ID = cocycles.MirroredInterstitialDCEL(D)

# Initial cross ratio set
X0 = np.ones(ID.nx) * 1.9

deriv_eps=1e-9
def fun(X):
    Yv = ID.packing_defect(X)
    A = ID.hol(chain_down,X)
    B = ID.hol(chain_right,X)
    C = A.dot(B)
    ta,tb,tab = [np.trace(m) for m in [A,B,A.dot(B)]]
    return np.append(Yv,[np.imag(ta),np.imag(tb),np.imag(tab)])

def jac(X):
    J = np.zeros((ID.ny+3,ID.nx))
    Y0 = fun(X)
    for i in range(ID.nx):
        deltaX = np.zeros(ID.nx)
        deltaX[i] = deriv_eps
        Y1 = fun(X + deltaX)
        Yprime = (Y1 - Y0) / deriv_eps
        J[:,i] = Yprime
    return J

print('Initial cross ratio vector:\n',X0,'\n')

print('SEARCHING for a Fuchsian circle packing.')
X = lsons.lsroot(fun, jac, X0, args=(), verbose=False, maxcond=1e10, maxiter=50, relax=1.0)
print('FOUND an apparent Fuchsian circle packing.\n')

print('Final cross ratio vector:\n',X,'\n')

A = ID.hol(chain_down,X)
B = ID.hol(chain_right,X)
C = A.dot(B)
x = np.trace(A)
y=np.trace(B)
z=np.trace(C)

print('Holonomy generators:')
print('A=',A)
print('B=',A)
print()

print('(tr(A), tr(B), tr(AB)) = ({},{},{})'.format(x,y,z))
print('tr([A,B]) = ',x*x+y*y+z*z-x*y*z-2)


print('\nHere are the six circles around some vertex:')
e0 = chain_down[3] # 3 levels below the top edge of the initial cylinder
c0 = circle.from_point_angle(0, 0) # Real line is C0 in the "standard interstice"
# This loop will enumerate circles which are the neighbors of v0 = e0.src
for i in range(6):
    chain = [e0]
    # Rotate i steps
    for k in range(i):
        chain.append(chain[-1].vert_cw)
    # Right now, v0 is still the marked vertex
    # Rotate within tri so that the marked one is now one of the neighbors of v0
    chain.append(chain[-1].tri_cw)

    # Chain assembled; compute its holonomy
    h = ID.hol(chain,X)
    # Apply to real axis
    c = c0.transform_gl2(h)
    # Report result
    print(c)

