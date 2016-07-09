"""Find a Fuchsian starting point then lift a path"""

import numpy as np
import circle
import cocycles
import triangulations
import dcel
import lsons
import sys
import mobius
from collections import defaultdict

np.set_printoptions(suppress=True)

D,t,b = triangulations.cylinder(10,10)
t2 = t.boundary_forward(5)
dcel.glue_boundary(D,t,b,t2)

# Freeze and index the DCEL
ID = cocycles.MirroredInterstitialDCEL(D)

# Make two holonomy chains (A and B generating pi_1)
# One (A) proceeds down from the top edge, the other (B) right
# Because of the gluing, A closes up
# Because we started with a cylinder, B closes up
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

# Set up a function fun:R^n -> R^k and a numerical derivative jac:R^n -> Mat(k,n)
# so that finding a zero of fun means finding a genuine circle packing

# In this case, most of the vector fun(X) consists of entries in the vertex products
# But we also append the imaginary parts of the holonomy traces, since we're looking
# for a REAL point.
hol_precond = 1000.0
deriv_eps=1e-12
def KAT_fun(LX):
    X = np.exp(LX)
    Yv = ID.packing_defect(X)
    A = ID.hol(chain_down,X)
    B = ID.hol(chain_right,X)
    tracevec = np.array( [np.trace(m) for m in [A,B,A.dot(B),A.dot(mobius.sl2inv(B))]] )
    return np.append(Yv,hol_precond*np.imag(tracevec))

KAT_jac = lambda x:lsons.numjac(KAT_fun,x)

def real_valence(v):
    if v.is_interior:
        return v.valence
    else:
        return 2*v.valence

def max_endpoint_valence(e):
    if e.twin:
        return max(real_valence(e.src),real_valence(e.dst))
    else:
        return max(real_valence(e.src),real_valence(e.boundary_next.src))

X0 = np.array([ circle.steiner_chain_xratio(max_endpoint_valence(e)) for e in ID.UE ])
LX0 = np.log(X0)
LX = lsons.lsroot(KAT_fun,KAT_jac,LX0,maxcond=1e20,maxiter=100,relax=0.5,normgoal=0.0001*np.sqrt(len(X0)),verbose=True)
X = np.exp(LX)


# Report a bit about the holonomy
A = ID.hol(chain_down,X)
B = ID.hol(chain_right,X)
C = A.dot(B)
x = np.trace(A)
y=np.trace(B)
z=np.trace(C)
m=x*x+y*y+z*z-x*y*z-2

print()
print('Holonomy generators:')
print('A=',A)
print('B=',B)
print()

print('(tr(A), tr(B), tr(AB)) = ({},{},{})'.format(x,y,z))
print('tr([A,B]) = ',m)

print()
if x.real < 2.0:
    print('LOOKS BAD: tr(A) < 2')
elif y.real < 2.0:
    print('LOOKS BAD: tr(B) < 2')
elif z.real < 2.0:
    print('LOOKS BAD: tr(AB) < 2')
elif abs(m) < 2:
    print('LOOKS BAD: [A,B] not hyperbolic')
elif m.real > 0:
    print('LOOKS BAD: tr([A,B]) positive (hence axis(A), axis(B) disjoint) ')
else:
    print('Holonomy ok (apparently Fuchsian)')


echains = dcel.edge_chain_dfs(D,t)
vchains = set()
vert_seen = set()
for ch in echains:
    if ch[-1].src not in vert_seen:
        vert_seen.add(ch[-1].src)  # <--- IMPORTANT TIME-WASTING BUG WAS FIXED HERE
        vchains.add(ch)
    
def normalized_developed_circles(LX):
    X = np.exp(LX)
    A = ID.hol(chain_down,X)
    B = ID.hol(chain_right,X)
    AI=mobius.sl2inv(A)
    BI=mobius.sl2inv(B)
    words = [np.eye(2), A, B, AI, BI, A.dot(B), A.dot(BI), B.dot(A), B.dot(AI), AI.dot(B), AI.dot(BI), BI.dot(A), BI.dot(AI) ]
    mnorm = mobius.center_two_hyperbolics(B,A)
    c0 = circle.from_point_angle(0,0) # Real line is C0 in the "standard interstice"
    dev_circles = set()
    for ch in vchains:
        h = ID.hol(ch,X)
        c = c0.transform_gl2(h)
        for w in words:
            cw = c.transform_sl2(w).transform_sl2(mnorm)
            if not cw.contains_infinity:
                yield (cw.center,cw.radius)

    
def rhovec(X):
    A = ID.hol(chain_down,X)
    B = ID.hol(chain_right,X)
    C = A.dot(B)
    return np.array([mobius.sl2_rho(m) for m in [A,B,C]])

def cxlen_fun(rgoal,LX):
    X = np.exp(LX)
    Yv = ID.packing_defect(X)
    A = ID.hol(chain_down,X)
    B = ID.hol(chain_right,X)
    deltar = rhovec(X) - rgoal
    return np.append(Yv,1000*deltar)

rdir = np.array([0.0,1.0,0.0])
tmax = 25.0
tstep = 0.01
outfnbase = "output/cxlen_run2/circles%.2f.txt"

r0 = rhovec(X)
for t in np.arange(0,tmax,tstep):
    rgoal = r0 + t*rdir
    fun = lambda x:cxlen_fun(rgoal,x)
    jac = lambda x:lsons.numjac(fun,x)
    LX = lsons.lsroot(fun,jac,LX,maxcond=1e20,maxiter=100,relax=1.0,normgoal=0.0001*np.sqrt(len(LX)),verbose=True)
    print('t=',t,'max(log(xrat))=',max(LX),'min(log(xrat))=',min(LX))
    with open(outfnbase % t,'wt') as outfile:
        for ctr,rad in normalized_developed_circles(LX):
            outfile.write('%f %f %f\n' % (ctr.real,ctr.imag,rad))


