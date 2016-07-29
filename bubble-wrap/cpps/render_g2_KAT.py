import sys

import cpps.circle as circle
import cpps.dcel as dcel
import cpps.mobius as mobius
import cpps.serialization as ser
import numpy as np

import cocycles as cocycles

if len(sys.argv) < 2:
    print('''ERROR: No input filename given.

USAGE: render_g2_KAT.py INFILE [OUTIMAGE]

INFILE should be a CPJ/CPZ file containing at least one circle packing
of a genus 2 surface which is either Fuchsian or nearly so, and with
stored edge chains labeled 'a1', 'b1', 'a2', 'b2' giving holonomy
generators.

The output file of find_g2_KAT.py would be an example of a possible
input file for this program.''')
    sys.exit(1)

infn = sys.argv[1]

if len(sys.argv) < 3:
    outfn = 'out.png'
    print('WARNING: Using default output filename "%s"' % outfn)
else:
    outfn = sys.argv[2]


meta,D,chains,P = ser.zloadfn(infn, cls=cocycles.InterstitialDCEL)
basept = chains['t1'][0]
X0 = P[0]

rho0 = {k:D.hol(chains[k],X0) for k in chains}

def commutator(a,b):
    return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))
def conjugate(inner,outer):
    return mobius.sl2inv(outer).dot(inner).dot(outer)

rho = {'a1':rho0['a1'],
       'b1':rho0['b1'],
       'a2':conjugate(rho0['a2'],rho0['b2']),
       'b2':rho0['b2']}

print('This should be the identity matrix:')
print(commutator(rho['a1'],rho['b1']).dot(commutator(rho['a2'],rho['b2'])))

from collections import defaultdict
verts_of_valence = defaultdict(int)
for v in D.V:
    verts_of_valence[v.valence] += 1
for k in verts_of_valence:
    print(verts_of_valence[k],'vertices of valence',k)

recip = np.array([[0,1j],[1j,0]])
fc = mobius.fix(commutator(rho['a1'], rho['b1']))
fa1 = mobius.fix(rho['a1'])
fa2 = mobius.fix(rho['a2'])
mnormKAT = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
mnormKAT = recip.dot(mnormKAT)

import fgrep as fgrep
Rho = fgrep.FreeGroup({'a':rho['a1'], 'b':rho['b1'], 'c':rho['a2'], 'd':rho['b2'],
                       'k':commutator(rho['a1'],rho['b1'])}, inverter=mobius.sl2inv)


import bz2
pared_wordlist = { x.strip() for x in bz2.open('data/words/g2-commgen-pared-norm50.txt.bz2','rt')}

print('Computing circle positions...')

echains = dcel.edge_chain_dfs(D, basept)
vchains = set()
vert_seen = set()
for ch in echains:
    if ch[-1].src not in vert_seen:
        vert_seen.add(ch[-1].src)
        vchains.add(ch)
c0 = circle.from_point_angle(0, 0) # Real line is C0 in the "standard interstice"
dev_pairs = set() # Will store (chain,holonomy word) pairs for general pictures later
dev_circles = set()  # Will store circles for the Fuchsian (KAT) picture
centers = dict()
for ch in vchains:
    h = D.hol(ch,X0)
    c1 = c0.transform_gl2(h)
    for w in pared_wordlist:
        c = c1.transform_sl2(Rho[w]).transform_sl2(mnormKAT)
        if not c.contains_infinity and c.radius > 0.005:
            dev_pairs.add((ch,w))
            dev_circles.add(c)

print('Generated %d circles' % len(dev_circles))

print('Drawing (with matplotlib)...')

import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (10.0, 8.0)

def empty_circle_cplx(z,r,color="blue"):
    e = plt.Circle((z.real,z.imag),r)
    ax = plt.gca()
    ax.add_artist(e)
    e.set_clip_box(ax.bbox)
    e.set_edgecolor(color)
    e.set_facecolor("none")

plt.figure(figsize=(10,10))
for c in dev_circles:
    empty_circle_cplx(c.center, c.radius)
empty_circle_cplx(0,1,color="black")
plt.ylim([-1,1])
plt.xlim([-1,1])
plt.gca().set_aspect("equal")

print('Saving "%s"' % outfn)
plt.savefig(outfn)
