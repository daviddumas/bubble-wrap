"""
Open a Circle Packing from a *.cpz file
"""

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from tools import *
import numpy as np
import cmath
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

    print("RHO:", rho0['a1'])

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

    # pared_wordlist = ["%s%s%s"%(a, b, c) for a in possi for b in possi for c in possi] + ["%s%s"%(a, b) for a in possi for b in possi] + ["%s"%a for a in possi]
    # pared_wordlist = ["kK", "C", "D", "CC", "Cd", "CD", "CB"]

    # print(pared_wordlist)

    echains = dcel.edge_chain_dfs(D, chains['t1'][0])
    vchains = set()
    vert_seen = set()
    for ch in echains:
        if ch[-1].src not in vert_seen:
            vert_seen.add(ch[-1].src)
            vchains.add(ch)

    findwords = FindWordsThread(parent, vchains, D, X0, Rho, mnormKAT)
    findwords.start()

    parent.mainWidget.opened_dcel = D


    ondone()


"""
The AnimationThread class animates transformations smoothly.

note that `self.parent().draw_trigger.emit()` is what updates the graphics
"""


class FindWordsThread(QThread):
    def __init__(self, parent, vchains, D, X0, Rho, mnormKAT):
        super().__init__(parent)

        self.vchains = vchains
        self.D = D
        self.X0 = X0
        self.Rho = Rho
        self.mnormKAT = mnormKAT

    def run(self):

        def getNormCenter(c):
            if c.contains_infinity:
                return complex(10e8, 10e8)
            return complex(int(c.center.real * 100000) / 100000, int(c.center.imag * 100000) / 100000)

        c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"

        self.parent().mainWidget.circles = []  # Will store circles for the Fuchsian (KAT) picture
        centers = []
        omit_centers = []

        # First add the Fundamental Domain
        for ch in self.vchains:
            h = self.D.hol(ch, self.X0)
            c1 = c0.transform_gl2(h).transform_sl2(self.mnormKAT)
            v0 = ch[-1].src
            self.parent().mainWidget.circles.append([c1, v0])
            omit_centers.append(getNormCenter(c1))

        # Then find the surrounding circles through holonomy
        for ch in self.vchains:
            h = self.D.hol(ch, self.X0)
            c1 = c0.transform_gl2(h)

            def testConfig(w):
                c = c1.transform_sl2(self.Rho[w]).transform_sl2(self.mnormKAT)
                if getNormCenter(c) not in centers:
                    centers.append(getNormCenter(c))
                    if getNormCenter(c) not in omit_centers and \
                            not c.contains_infinity and \
                                    np.abs(c.radius) >= 0.005 or c.contains_infinity:
                        v0 = ch[-1].src
                        self.parent().mainWidget.circles.append([c, v0])

                    if not c.contains_infinity and np.abs(c.radius) < 0.00025:
                        return False

                    return True

                return False

            def find_word(w_list="aAbBcCdDkK", w="", n=7):
                """
                finds as many 'words' as possible to fill the circle packing
                :param w: current word
                :param n: recursion depth
                """
                if n > 0:
                    for w_n in w_list:
                        if testConfig(w + w_n):
                            find_word(w_list, w + w_n, n - 1)

            find_word()
            self.parent().draw_trigger.emit()