"""
Open a Circle Packing from a *.cpz file
"""

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from tools import *
import numpy as np
from collections import OrderedDict

from cpps import serialization as ser, dcel, cocycles, mobius, circle

def openPacking(parent, ondone):
    file = QFileDialog.getOpenFileName(parent=parent)
    if file[0] == None or len(file[0]) < 5:
        return
    print(len(file[0]))
    print("Open a new file: %s" % str(file[0]))

    meta, D, chains, P = ser.zloadfn(file[0], cls=cocycles.InterstitialDCEL)

    if isinstance(P, list):
        print("here")
        tempP = P.copy()
        P={}
        for i in range(len(tempP)):
            P[str("Packing %d"%i)] = tempP[i]

    odict = OrderedDict.fromkeys(P)
    mkey = showListDialog(parent, odict)
    if isinstance(mkey, int) and mkey == -1:
        return
    X0 = P[mkey]

    def commutator(a, b):
        return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))

    def conjugate(inner, outer):
        return mobius.sl2inv(outer).dot(inner).dot(outer)

    recip = np.array([[0, 1j], [1j, 0]])

    print('Computing circle positions...')

    echains = dcel.edge_chain_dfs(D, chains['t1'][0])
    vchains = set()
    vert_seen = set()
    for ch in echains:
        if ch[-1].src not in vert_seen:
            vert_seen.add(ch[-1].src)
            vchains.add(ch)
    c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"
    dev_chains = set()  # Will store (chain,holonomy word) pairs for general pictures later
    for ch in vchains:
        h = D.hol(ch, X0)
        c = c0.transform_gl2(h)
        if not c.contains_infinity and c.radius > .005:
            dev_chains.add(ch)

    def show_fund(DD, edge_chains, X):
        rho0 = {k: DD.hol(edge_chains[k], X) for k in ['a1', 'a2', 'b1', 'b2']}
        rho = {'a1': rho0['a1'],
               'b1': rho0['b1'],
               'a2': conjugate(rho0['a2'], rho0['b2']),
               'b2': rho0['b2']}
        fc = mobius.fix(commutator(rho['a1'], rho['b1']))
        fa1 = mobius.fix(rho['a1'])
        fa2 = mobius.fix(rho['a2'])
        mnorm = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
        mnorm = recip.dot(mnorm)
        output_circles = []
        for ch in dev_chains:
            h = DD.hol(ch, X)
            c = c0.transform_gl2(h).transform_sl2(mnorm)
            if c.radius > .005:
                output_circles.append(c)
                print('Generated %d circles' % len(output_circles))
                parent.mainWidget.circles = output_circles

    show_fund(D, chains, X0)
    # for c in self.mainWidget.circles:
    #     c.transform_sl2(((0.0001,0),
    #                      (0,1)))
    ondone()