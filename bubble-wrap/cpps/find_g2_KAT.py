"""Find the KAT point for a genus two surface and save it"""

import cpps.circle as circle
import cpps.cocycles as cocycles
import cpps.dcel as dcel
import cpps.mobius as mobius
import cpps.serialization as ser
import cpps.triangulations as triangulations
import numpy as np

import lsons as lsons

np.set_printoptions(suppress=True)

mD1,t1,b1 = triangulations.cylinder(5, 5)
t1stop = t1.boundary_forward(1)
dcel.glue_boundary(mD1, t1, b1, t1stop)

mD2,t2,b2 = triangulations.cylinder(5, 5)
t2stop = t2.boundary_forward(1)
dcel.glue_boundary(mD2, t2, b2, t2stop)

dcel.reverse_orientation(mD2)
mD = mD1 | mD2
dcel.glue_boundary(mD, t1stop, t2stop)

# Freeze and index the DCEL
D = cocycles.InterstitialDCEL(mD)

# Make holonomy generators
# Two of the generators are easy starting from t1
# And two are easy starting from t2
# To glue them we need a path from t1 to t2

t1_to_t2 = [t1]
for i in range(5):
    t1_to_t2.append(t1_to_t2[-1].vert_ccw)
t1_to_t2.append(t1_to_t2[-1].tri_cw)
assert t1_to_t2[-1] == t2 # We made it.

def cyl_move_down(ch):
    e = ch[-1]
    a = e.tri_cw
    b = a.vert_ccw
    c = b.vert_ccw
    return ch + [a,b,c]

def cyl_move_up(ch):
    e = ch[-1]
    a = e.vert_cw
    b = a.vert_cw
    c = b.tri_ccw
    return ch + [a,b,c]

def cyl_move_right(ch):
    e = ch[-1]
    a = e.vert_ccw
    b = a.vert_ccw
    c = b.tri_cw
    return ch + [a,b,c]

def cyl_move_left(ch):
    e = ch[-1]
    a = e.tri_ccw
    b = a.vert_cw
    c = b.vert_cw
    return ch + [a,b,c]

chA1 = [t1]
while True:
    chA1 = cyl_move_right(chA1)
    if chA1[-1] == t1:
        break        

chB1 = [t1]
while True:
    chB1 = cyl_move_up(chB1)
    if chB1[-1] == t1:
        break        

chA2_0 = [t2]
while True:
    chA2_0 = cyl_move_left(chA2_0)
    if chA2_0[-1] == t2:
        break

chB2_0 = [t2]
while True:
    chB2_0 = cyl_move_down(chB2_0)
    if chB2_0[-1] == t2:
        break        

chains = {
    'a1':chA1,
    'b1':chB1,
    'a2':t1_to_t2[:-1]+chA2_0+t1_to_t2[-2::-1],
    'b2':t1_to_t2[:-1]+chB2_0+t1_to_t2[-2::-1],
}

# Set up a function fun:R^n -> R^k and a numerical derivative jac:R^n -> Mat(k,n)
# so that finding a zero of fun means finding a genuine circle packing

# In this case, most of the vector fun(X) consists of entries in the vertex products
# But we also append the imaginary parts of the holonomy traces, since we're looking
# for a REAL point.
hol_precond = 1000.0
deriv_eps=1e-12
def KAT_fun(LX):
    X = np.exp(LX)
    Yv = D.packing_defect(X)
    hols = {k:D.hol(chains[k],X) for k in chains}
    tracevec = np.array( [np.trace(m) for m in
                          [
                              hols['a1'],
                              hols['b1'],
                              hols['a1'].dot(hols['b1']),
                              hols['a2'],
                              hols['b2'],
                              hols['a2'].dot(hols['b2']),
                              hols['a1'].dot(hols['b2']),
                              hols['a2'].dot(hols['b1']),
                          ]
                         ])
    return np.append(Yv,hol_precond*np.imag(tracevec))

KAT_jac = lambda x: lsons.numjac(KAT_fun, x)


def max_endpoint_valence(e):
    return max(e.src.valence,e.dst.valence)

def avg_endpoint_valence(e):
    return 0.5*(e.src.valence + e.dst.valence)

def large_norm_quit(x,y,n):
    if n > 1e7:
        raise Exception('Norm too large')

X0 = np.array([circle.steiner_chain_xratio(max_endpoint_valence(e)) for e in D.UE])
LX0 = np.log(X0)
LX = lsons.lsroot(KAT_fun, KAT_jac, LX0, maxcond=1e20, maxiter=200, relax=0.6, normgoal=np.sqrt(len(X0)), verbose=True, monitor=large_norm_quit)
LX = lsons.lsroot(KAT_fun, KAT_jac, LX, maxcond=1e20, maxiter=200, relax=1.0, normgoal=1e-10 * np.sqrt(len(X0)), verbose=True, monitor=large_norm_quit)
X = np.exp(LX)

# Report a bit about the holonomy
hols = {k:D.hol(chains[k],X) for k in chains}

def show_hol_elt(dct,k):
#    print('%s=' % k,dct[k])
    print('tr(%s)=' % k,np.trace(dct[k]))

def commutator(a,b):
    return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))
    
print()
print('Holonomy generators:')
show_hol_elt(hols,'a1')
show_hol_elt(hols,'b1')
show_hol_elt(hols,'a2')
show_hol_elt(hols,'b2')
hols['c1'] = commutator(hols['a1'],hols['b1'])
hols['c2'] = commutator(hols['a2'],hols['b2'])
show_hol_elt(hols,'c1')
show_hol_elt(hols,'c2')

print(hols['c1'].dot(hols['c2']))

chains['t1'] = [ t1 ]
chains['t2'] = [ t2 ]

ser.zstorefn('output/KAT/g2-5x5-c8.KAT.cpz',D,chains,[X])
