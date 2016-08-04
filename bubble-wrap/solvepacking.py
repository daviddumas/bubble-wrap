import numpy as np
import circle as circle
import lsons as lsons
import mobius as mobius
import serialization as ser

def from_torus_and_save(D, fn):
    # Make holonomy generators
    # Two of the generators are easy starting from t1
    try:
        def cyl_move_down(ch):
            e = ch[-1]
            a = e.tri_cw
            b = a.vert_ccw
            c = b.vert_ccw
            return ch + [a, b, c]

        def cyl_move_up(ch):
            e = ch[-1]
            a = e.vert_cw
            b = a.vert_cw
            c = b.tri_ccw
            return ch + [a, b, c]

        def cyl_move_right(ch):
            e = ch[-1]
            a = e.vert_ccw
            b = a.vert_ccw
            c = b.tri_cw
            return ch + [a, b, c]

        def cyl_move_left(ch):
            e = ch[-1]
            a = e.tri_ccw
            b = a.vert_cw
            c = b.vert_cw
            return ch + [a, b, c]

        chA1 = [D.e1]
        while True:
            chA1 = cyl_move_right(chA1)
            if chA1[-1] == D.e1:
                break

        chB1 = [D.e1]
        while True:
            chB1 = cyl_move_up(chB1)
            if chB1[-1] == D.e1:
                break

        chains = {
            'a1': chA1,
            'b1': chB1
        }

        # Set up a function fun:R^n -> R^k and a numerical derivative jac:R^n -> Mat(k,n)
        # so that finding a zero of fun means finding a genuine circle packing

        # In this case, most of the vector fun(X) consists of entries in the vertex products
        # But we also append the imaginary parts of the holonomy traces, since we're looking
        # for a REAL point.
        hol_precond = 1000.0
        deriv_eps = 1e-12

        def KAT_fun(LX):
            X = np.exp(LX)
            Yv = D.packing_defect(X)
            hols = {k: D.hol(chains[k], X) for k in chains}
            tracevec = np.array([np.trace(m) for m in
                                 [
                                     hols['a1'],
                                     hols['b1'],
                                     hols['a1'].dot(hols['b1'])
                                 ]
                                 ])
            return np.append(Yv, hol_precond * np.imag(tracevec))

        KAT_jac = lambda x: lsons.numjac(KAT_fun, x)

        def max_endpoint_valence(e):
            return max(e.src.valence, e.dst.valence)

        def avg_endpoint_valence(e):
            return 0.5 * (e.src.valence + e.dst.valence)

        def large_norm_quit(x, y, n):
            if n > 1e7:
                raise Exception('Norm too large')

        X0 = np.array([circle.steiner_chain_xratio(max_endpoint_valence(e)) for e in D.UE])
        LX0 = np.log(X0)
        LX = lsons.lsroot(KAT_fun, KAT_jac, LX0, maxcond=1e20, maxiter=200, relax=0.6, normgoal=np.sqrt(len(X0)),
                          verbose=True, monitor=large_norm_quit)
        LX = lsons.lsroot(KAT_fun, KAT_jac, LX, maxcond=1e20, maxiter=200, relax=1.0, normgoal=1e-10 * np.sqrt(len(X0)),
                          verbose=True, monitor=large_norm_quit)
        X = np.exp(LX)

        # Report a bit about the holonomy
        hols = {k: D.hol(chains[k], X) for k in chains}

        def show_hol_elt(dct, k):
            #    print('%s=' % k,dct[k])
            print('tr(%s)=' % k, np.trace(dct[k]))

        def commutator(a, b):
            return a.dot(b).dot(mobius.sl2inv(a)).dot(mobius.sl2inv(b))

        print()
        print('Holonomy generators:')
        show_hol_elt(hols, 'a1')
        show_hol_elt(hols, 'b1')
        hols['c1'] = commutator(hols['a1'], hols['b1'])
        show_hol_elt(hols, 'c1')

        #print(hols['c1'].dot(hols['c2']))

        chains['t1'] = [D.e1]
    except:
        print("error while solving circle packing.")
        return

    try:
        ser.zstorefn(fn, D, chains, [X])
    except:
        print("There was an error storing the file")
