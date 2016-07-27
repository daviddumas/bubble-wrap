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

    # SHOW DIALOG
    if isinstance(P, list):
        tempP = P.copy()
        P={}
        for i in range(len(tempP)):
            P[str("Packing %d"%i)] = tempP[i]

    try:
        odict = OrderedDict.fromkeys(sorted(P, key=lambda x: float(x)))
    except(Exception):
        odict = OrderedDict.fromkeys(sorted(P))

    mkey = showListDialog(parent, odict, "Select a Packing")
    if isinstance(mkey, int) and mkey == -1:
        return
    X0 = P[mkey]

    # SOLVE
    rho0 = {k: D.hol(chains[k], X0) for k in ['a1', 'a2', 'b1', 'b2']}

    def commutator(a, b):
        return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))

    def conjugate(inner, outer):
        return mobius.sl2inv(outer).dot(inner).dot(outer)

    rho = {'a1': rho0['a1'],
           'b1': rho0['b1'],
           'a2': conjugate(rho0['a2'], rho0['b2']),
           'b2': rho0['b2']}

    print('This should be the identity matrix:')
    print(commutator(rho['a1'], rho['b1']).dot(commutator(rho['a2'], rho['b2'])))

    from collections import defaultdict
    verts_of_valence = defaultdict(int)
    for v in D.V:
        verts_of_valence[v.valence] += 1
    for k in verts_of_valence:
        print(verts_of_valence[k], 'vertices of valence', k)

    recip = np.array([[0, 1j], [1j, 0]])
    fc = mobius.fix(commutator(rho['a1'], rho['b1']))
    fa1 = mobius.fix(rho['a1'])
    fa2 = mobius.fix(rho['a2'])
    mnormKAT = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
    mnormKAT = recip.dot(mnormKAT)

    import cpps.fgrep as fgrep
    Rho = fgrep.FreeGroup({'a': rho['a1'], 'b': rho['b1'], 'c': rho['a2'], 'd': rho['b2'],
                           'k': commutator(rho['a1'], rho['b1'])}, inverter=mobius.sl2inv)

    print('Computing circle positions...')

    echains = dcel.edge_chain_dfs(D, chains['t1'][0])
    vchains = set()
    vert_seen = set()
    for ch in echains:
        if ch[-1].src not in vert_seen:
            vert_seen.add(ch[-1].src)
            vchains.add(ch)
    c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"
    dev_pairs = set()  # Will store (chain,holonomy word) pairs for general pictures later
    dev_circles = []  # Will store circles for the Fuchsian (KAT) picture
    centers = dict()
    for ch in vchains:
        h = D.hol(ch, X0)
        c1 = c0.transform_gl2(h).transform_sl2(mnormKAT)
        if not c1.contains_infinity and c1.radius > 0.005 or c1.contains_infinity:
            v0 = ch[-1].src
            dev_circles.append([c1, v0])
    parent.mainWidget.circles = list(dev_circles)
    parent.mainWidget.opened_dcel = D




    # def commutator(a, b):
    #     return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))
    #
    # def conjugate(inner, outer):
    #     return mobius.sl2inv(outer).dot(inner).dot(outer)
    #
    # recip = np.array([[0, 1j], [1j, 0]])
    #
    # rho0 = {k: D.hol(chains[k], X0) for k in ['a1', 'a2', 'b1', 'b2']}
    # rho = {'a1': rho0['a1'],
    #        'b1': rho0['b1'],
    #        'a2': conjugate(rho0['a2'], rho0['b2']),
    #        'b2': rho0['b2']}
    #
    # print('Computing circle positions...')
    #
    # echains = dcel.edge_chain_dfs(D, chains['t1'][0])
    # vchains = set()
    # vert_seen = set()
    # for ch in echains:
    #     if ch[-1].src not in vert_seen:
    #         vert_seen.add(ch[-1].src)
    #         vchains.add(ch)
    # c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"
    # dev_chains = set()  # Will store (chain,holonomy word) pairs for general pictures later
    # for ch in vchains:
    #     h = D.hol(ch, X0)
    #     c = c0.transform_gl2(h)
    #     if not c.contains_infinity and c.radius > .005:
    #         dev_chains.add(ch)
    #
    #
    # fc = mobius.fix(commutator(rho['a1'], rho['b1']))
    # fa1 = mobius.fix(rho['a1'])
    # fa2 = mobius.fix(rho['a2'])
    # mnorm = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
    # mnorm = recip.dot(mnorm)
    # output_circles = []
    # for ch in dev_chains:
    #     h = D.hol(ch, X0)
    #     c = c0.transform_gl2(h).transform_sl2(mnorm)
    #     if c.radius > .005:
    #         output_circles.append(c)
    #         print('Generated %d circles' % len(output_circles))
    # parent.mainWidget.circles = output_circles

    ondone()