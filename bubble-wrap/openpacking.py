"""
Open a Circle Packing from a *.cpz file
"""

import bz2
from collections import OrderedDict

import circle
import cocycles
import dcel
import serialization as ser
from tools import *

import assets

def openPacking(parent, delegate, ondone):
    """
    Open a circle packing with genus 1 or 2
    :param parent:
    :param ondone:
    :return:
    """
    # set unified embedded circle packing holder
    uecp = delegate.uecp

    file = QFileDialog.getOpenFileName(parent=parent, initialFilter="CPZ (*.cpz)")
    if file[0] is None or len(file[0]) < 5:
        return
    print(len(file[0]))
    print("Open a new file: %s" % str(file[0]))
    try:
        meta, D, chains, P = ser.zloadfn(file[0], cls=cocycles.InterstitialDCEL)
    except(Exception):
        print("Unable to open file.  Is the file a *.cpz?")
        return

    odict = ordered_packing_list(P)

    # displays a drop down menu with all available circle packings
    mkey = showDropdownDialog(parent, odict, "Select a Packing")

    model = standardModelFromDict(parent, odict)
    delegate.select_packing_dropdown.setModel(model)

    uecp.opened_metadata = meta
    uecp.opened_dcel = D
    uecp.all_packings = P
    uecp.chains = chains

    find_simplest_packing_for_pure_dual_graph(delegate, odict)

    from_select_packing(parent, delegate, mkey, ondone)

def find_simplest_packing_for_pure_dual_graph(delegate, odict):
    uecp = delegate.uecp
    closest_xratio = None
    closest_id = None
    for key in odict:
        xratio2_sum = 0
        for xratio in list(odict[key]):
            xratio2_sum += (xratio-1.7320508)**2
        xratio2_avg = xratio2_sum / len(list(odict[key]))
        if closest_xratio is None or closest_xratio > xratio2_avg:
            closest_xratio = xratio2_avg
            closest_id = key

    # start building fundamental domain
    X0 = odict[closest_id]

    # SOLVE
    if dcel.oriented_manifold_type(uecp.opened_dcel)['genus'] == 2:
        # genus 2
        pure_fund_domain_genus2(delegate, uecp.opened_dcel, uecp.chains, X0)
    elif dcel.oriented_manifold_type(uecp.opened_dcel)['genus'] == 1:
        # genus 1 (torus)
        pure_fund_domain_genus1(delegate, uecp.opened_dcel, uecp.chains, X0)

    #print(closest_id, closest_xratio, X0)

    pass

def from_select_packing(parent, delegate, mkey, ondone):
    # set unified embedded circle packing holder
    uecp = delegate.uecp

    pared_wordlist = {x.strip() for x in bz2.open(assets.wordfile, 'rt')}

    odict = ordered_packing_list(uecp.all_packings)

    if isinstance(mkey, int) and mkey == -1:
        return
    elif isinstance(uecp.all_packings, dict):
        X0 = uecp.all_packings[str(list(odict.keys())[mkey])]
    else:
        X0 = uecp.all_packings[mkey]

    print(X0)

    # SOLVE
    if dcel.oriented_manifold_type(uecp.opened_dcel)['genus'] == 2:
        # genus 2
        open_genus2(parent, delegate, uecp.opened_dcel, uecp.chains, X0, ondone=ondone, words=pared_wordlist)
    elif dcel.oriented_manifold_type(uecp.opened_dcel)['genus'] == 1:
        # genus 1 (torus)
        open_genus1(parent, delegate, uecp.opened_dcel, uecp.chains, X0, ondone=ondone)

def ordered_packing_list(P):
    # SHOW Packing DIALOG
    if isinstance(P, list):
        tempP = P.copy()
        P = {}
        for i in range(len(tempP)):
            P[str("Packing %d" % i)] = tempP[i]
    try:
        odict = OrderedDict.fromkeys(sorted(P, key=lambda x: float(x)))
    except(Exception):
        odict = OrderedDict.fromkeys(sorted(P))

    for key in odict:
        odict[key] = list(P[key])
    return odict

def open_genus2(parent, delegate, D, chains, X0, ondone, words=None):
    """
    Find a circle packing for a genus 2 surface
    :param parent:
    :param D:
    :param chains:
    :param X0:
    :param ondone:
    :param words:
    :return:
    """

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

    import fgrep as fgrep
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

    findwords = FindWordsThread(parent, delegate, vchains, D, X0, Rho, mnormKAT, known_words=words)
    findwords.start()

    ondone()

def open_genus1(parent, delegate, D, chains, X0, ondone, words=None):
    """
    Find a circle packing for a genus 1 surface (torus)
    :param parent:
    :param D:
    :param chains:
    :param X0:
    :param ondone:
    :param words:
    :return:
    """

    rho0 = {k: D.hol(chains[k], X0) for k in ['a1', 'b1']}

    def commutator(a, b):
        return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))

    def conjugate(inner, outer):
        return mobius.sl2inv(outer).dot(inner).dot(outer)

    rho = {'a1': rho0['a1'],
           'b1': rho0['b1']}

    print("RHO:", rho0['a1'])

    print('This should be the identity matrix:')
    print(commutator(rho['a1'], rho['b1']))

    from collections import defaultdict
    verts_of_valence = defaultdict(int)
    for v in D.V:
        verts_of_valence[v.valence] += 1
    for k in verts_of_valence:
        print(verts_of_valence[k], 'vertices of valence', k)

    # recip = np.array([[0, 1j], [1j, 0]])
    # fc = mobius.fix(commutator(rho['a1'], rho['b1']))
    # fa1 = mobius.fix(rho['a1'])
    # mnormKAT = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
    # mnormKAT = recip.dot(mnormKAT)
    ident = np.array([[1, 0], [0, 1]])
    # normalize the circle packing to the viewport
    mob_zoom = np.array(((100, 0), (0, 0.01)), dtype='complex')

    import fgrep as fgrep
    Rho = fgrep.FreeGroup({'a': rho['a1'], 'b': rho['b1']}, inverter=mobius.sl2inv)

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

    findwords = FindWordsThread(parent, delegate, vchains, D, X0, Rho, ident, char_list="aAbB")
    findwords.start()

    ondone()

def pure_fund_domain_genus2(delegate, D, chains, X0):
    """
    Find a circle packing for a genus 2 surface
    :param parent:
    :param D:
    :param chains:
    :param X0:
    :param ondone:
    :param words:
    :return:
    """
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

    import fgrep as fgrep
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

    uecp = delegate.uecp
    c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"
    uecp.pure_dual_graph_circles = []

    for ch in vchains:
        h = D.hol(ch, X0)
        c1 = c0.transform_gl2(h).transform_sl2(mnormKAT)
        v0 = ch[-1].src
        uecp.pure_dual_graph_circles.append([c1, v0, True])

def pure_fund_domain_genus1(delegate, D, chains, X0):
    """
    Find a circle packing for a genus 1 surface (torus)
    :param parent:
    :param D:
    :param chains:
    :param X0:
    :param ondone:
    :param words:
    :return:
    """

    rho0 = {k: D.hol(chains[k], X0) for k in ['a1', 'b1']}

    def commutator(a, b):
        return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))

    def conjugate(inner, outer):
        return mobius.sl2inv(outer).dot(inner).dot(outer)

    rho = {'a1': rho0['a1'],
           'b1': rho0['b1']}

    print("RHO:", rho0['a1'])

    print('This should be the identity matrix:')
    print(commutator(rho['a1'], rho['b1']))

    from collections import defaultdict
    verts_of_valence = defaultdict(int)
    for v in D.V:
        verts_of_valence[v.valence] += 1
    for k in verts_of_valence:
        print(verts_of_valence[k], 'vertices of valence', k)

    # recip = np.array([[0, 1j], [1j, 0]])
    # fc = mobius.fix(commutator(rho['a1'], rho['b1']))
    # fa1 = mobius.fix(rho['a1'])
    # mnormKAT = mobius.center_four_points(fc[0], fa1[0], fc[1], fa2[0])
    # mnormKAT = recip.dot(mnormKAT)
    mnormKAT = np.array([[1, 0], [0, 1]])
    # normalize the circle packing to the viewport

    import fgrep as fgrep
    Rho = fgrep.FreeGroup({'a': rho['a1'], 'b': rho['b1']}, inverter=mobius.sl2inv)

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

    uecp = delegate.uecp
    c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"
    uecp.pure_dual_graph_circles = []

    for ch in vchains:
        h = D.hol(ch, X0)
        c1 = c0.transform_gl2(h)
        v0 = ch[-1].src
        uecp.pure_dual_graph_circles.append([c1, v0, True])

class FindWordsThread(QThread):
    """
    Find and Display the words of a circle packing in a separate thread so that the UI is not bogged down
    """
    def __init__(self, parent, delegate, vchains, D, X0, Rho, mnormKAT, char_list="", known_words=None):
        super().__init__(parent)

        self.vchains = vchains
        self.D = D
        self.X0 = X0
        self.Rho = Rho
        self.mnormKAT = mnormKAT
        self.char_list = char_list
        self.known_words = known_words

        # set unified embedded circle packing holder
        self.uecp = delegate.uecp
        self.delegate = delegate

    def run(self):

        def getNormCenter(c):
            """
            Normalizes circle center by rounding it's coordinates
            :param c:
            :return:
            """
            if c.contains_infinity:
                return None
            return complex(int(c.center.real * 100000) / 100000, int(c.center.imag * 100000) / 100000)

        c0 = circle.from_point_angle(0, 0)  # Real line is C0 in the "standard interstice"

        # TODO: maybe use a reset function for these?
        self.uecp.circles = []  # Will store circles for the Fuchsian (KAT) picture
        self.uecp.circles_optimize = [[]]

        centers = []
        omit_circles = []

        # solve fundamental domain first (for dual graph)
        for ch in self.vchains:
            h = self.D.hol(ch, self.X0)
            c1 = c0.transform_gl2(h).transform_sl2(self.mnormKAT)
            v0 = ch[-1].src
            self.uecp.circles.append([c1, v0, True])
            omit_circles.append(getNormCenter(c1))

        # If there are no known words, calculate them here
        if self.known_words is None:
            # Then find the surrounding circles through holonomy
            for i, ch in enumerate(self.vchains):
                h = self.D.hol(ch, self.X0)
                c1 = c0.transform_gl2(h)

                def testConfig(w):
                    """
                    Given a word `w`, find whether or not the circle belongs in the packing
                    :param w: a word
                    :return:
                    """
                    c = c1.transform_sl2(self.Rho[w]).transform_sl2(self.mnormKAT)
                    norm = getNormCenter(c)
                    if norm not in omit_circles and (norm is None or norm not in centers):
                        if norm is not None:
                            centers.append(norm)
                        else:
                            print("line")
                        if not c.contains_infinity and np.abs(c.radius) >= 0.005 or c.contains_infinity:
                            v0 = ch[-1].src
                            self.uecp.circles.append([c, v0, False])

                        if not c.contains_infinity and np.abs(c.radius) < 0.00025:
                            return False

                        return True

                    return False

                def find_word(w_list="aAbBcCdD", w="", n=7):
                    """
                    finds as many 'words' as possible to fill the circle packing
                    :param w_list: list of word elements to build the words
                    :param w: current word
                    :param n: recursion depth
                    """
                    if n > 0:
                        for w_n in w_list:
                            if testConfig(w + w_n):
                                find_word(w_list, w + w_n, n - 1)

                find_word(w_list=self.char_list)

                # reflect progress on progress bar
                self.uecp.progressValue[0] = int((i + 1) / len(self.vchains) * 100)
                self.parent().draw_trigger.emit()
        else:
            # If the words are known, iterate over all words
            for i, ch in enumerate(self.vchains):
                h = self.D.hol(ch, self.X0)
                c1 = c0.transform_gl2(h)
                for w in self.known_words:
                    c = c1.transform_sl2(self.Rho[w]).transform_sl2(self.mnormKAT)
                    if getNormCenter(c) not in omit_circles:
                        v0 = ch[-1].src
                        self.uecp.circles.append([c, v0, False])

                # reflect progress on progress bar
                        self.uecp.progressValue[0] = int((i + 1) / len(self.vchains) * 100)
                self.parent().draw_trigger.emit()

        # Force update will require the UI to optimize the circle packing for snappy interaction
        self.delegate.graphics.force_update()
        # Tell the UI to redraw
        self.parent().draw_trigger.emit()
