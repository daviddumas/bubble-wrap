import numpy as np

import cocycles
import lsons
import serialization as ser

np.set_printoptions(suppress=True)
meta,D,ch,P = ser.zloadfn('output/KAT/g2-5x5-c4.KAT-cand6.cpz',cls=cocycles.InterstitialDCEL)
t1 = ch['t1'][0]
t2 = ch['t2'][0]
X0 = P[0]

def cyl_down(e):
    a = e.tri_cw
    b = a.vert_ccw
    c = b.vert_ccw
    return c

def cyl_right(e):
    a = e.vert_ccw
    b = a.vert_ccw
    c = b.tri_cw
    return c

def cyl_up(e):
    a = e.vert_cw
    b = a.vert_cw
    c = b.tri_ccw
    return c

def cyl_left(e):
    a = e.tri_ccw
    b = a.vert_cw
    c = b.vert_cw
    return c


m1a = cyl_right(cyl_right(cyl_down(cyl_down(t1))))
m1b = m1a.vert_ccw.vert_ccw
m1c = m1b.vert_ccw.vert_ccw

m2a = cyl_left(cyl_left(cyl_up(cyl_up(t2))))
m2b = m2a.vert_cw.vert_cw
m2c = m2b.vert_cw.vert_cw

ch['fixed_edges'] = [m1a,m1b,m1c,m2a,m2b,m2c]

fixed_indices = [ e.uidx for e in [m1a,m1b,m1c,m2a,m2b,m2c] ]
free_indices = [ i for i in range(D.nx) if i not in fixed_indices ]
invperm = np.argsort(fixed_indices + free_indices)

def deform_fun(LXfix,LXfree):
    LXperm = np.append(LXfix,LXfree)
    LX = np.array([LXperm[i] for i in invperm])
    X = np.exp(LX)
    Y = D.packing_defect(X)
    return Y

LX0 = np.log(X0)
LXfix0 = np.array( [ LX0[i] for i in fixed_indices ] )
LXfree0 = np.array( [ LX0[i] for i in free_indices ] )

epsilon = 1.0 / (D.nx**2)
print('epsilon=',epsilon)


def lift_path(f,xfix_path,xfree0,t0,t1,tstep,normgoal=1e-5):
    xfree = xfree0
    for t in np.arange(t0,t1,tstep):
        xfix = xfix_path(t)
        print('t=',t,'fix=',xfix)
        fun = lambda t:f(xfix,t)
        jac = lambda t:lsons.numjac(fun,t)
        xfree = lsons.lsroot(fun,jac,xfree,maxcond=1e20,maxiter=200,relax=0.8,normgoal=normgoal,verbose=True)
        yield t,xfree


def gamma(t):
    return LXfix0 + t*1e5*epsilon*np.array([0,0,1,0,0,-1])

print('GOAL: t=%f, xfix=%s',(1,str(gamma(1))))
vectors = []

try:
    for t,LXfree in lift_path(deform_fun,gamma,LXfree0,0,1,0.0002,normgoal=1e-8*np.sqrt(len(X0))):
        LXperm = np.append(gamma(t),LXfree)
        LX = np.array([LXperm[i] for i in invperm])
        X = np.exp(LX)
        vectors.append( (t,X) )
        print('max(X) = %f, min(X) = %f' % (max(X),min(X)))
except lsons.SolverException as e:
    print('Aborting on exception: ',e)

print('Final t=',t)

packings = dict(vectors)
    
ser.zstorefn('output/g2deform-run1/g2deform-m1c-m2C-1e5.cpz',D,edge_lists=ch,packings=packings,meta={'description':'Prescribed deformation of six edges (alternating triples abc at two vertices, m1 and m2); this path increases m1c and decreases m2C.'})

