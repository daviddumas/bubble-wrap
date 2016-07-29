import circle as circle
import mobius as mobius
import serialization as ser
import numpy as np
from PyQt5.QtCore import *

import lsons as lsons
from interpolators import *


def solve_circle_packing_from_torus(D):

    # Make holonomy generators
    # Two of the generators are easy starting from t1
    # And two are easy starting from t2
    # To glue them we need a path from t1 to t2

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

    ser.zstorefn('output/torus/torus.cpz', D, chains, [X])

class ControlCalculations(QObject):

    # This trigger will be used to update the graphics every frame.  At the moment it is arbitrary
    draw_trigger = pyqtSignal()

    def __init__(self, delegate):
        super().__init__(parent=delegate)
        self.delegate = delegate

        # Bind the buttons from the UI
        self.bind_btn(delegate.testbtn1)
        self.bind_btn(delegate.invert_pack_btn)
        self.bind_btn(delegate.testbtn3)
        self.bind_btn(delegate.reset_trans_btn)
        self.bind_btn(delegate.solve_btn)
        self.bind_btn(delegate.dual_graph_btn)
        self.adjustCircles(16)


    def bind_btn(self, btn):
        btn.clicked.connect(lambda: self.btn_clicked(btn))

    def adjustCircles(self, num_of_circles):
        side = int(math.sqrt(num_of_circles))
        scale = 1/side
        # Bind Data Structures
        # self.delegate.circles = [[c.from_center_radius(complex(x * scale, cmath.sqrt(3) * scale/2 * y) if y % 2 == 0 else
        #                                               complex(x * scale + scale/2, cmath.sqrt(3) * scale/2 * y), scale/2), CoordinateVertex()]
        #                          for x in range(-side//2, side//2+1) for y in range(-side//2, side//2+1)]

        #self.delegate.graphics.draw()

    def btn_clicked(self, btn):
        T = ((1.005 + 1.005j, 0.01),
             (0.5, 1 + 0.5j))

        d = self.delegate
        if btn == d.testbtn1:
            self.adjust_all(T)
        elif btn == d.testbtn3:
            self.animate_all(T)

        elif btn == d.invert_pack_btn:
            self.animate_all(np.array([[0, 1j], [1j, 0]]))
        elif btn == d.reset_trans_btn:
            self.animate_all(np.linalg.inv(d.packing_trans[0]))

        elif btn == d.dual_graph_btn:
            self.delegate.dual_graph = d.dual_graph_btn.isChecked()
            self.delegate.graphics.draw()

        elif btn == d.solve_btn:
            solve_circle_packing_from_torus(self.delegate.m_dcel)



    """
    The following methods apply either an transformation adjustment or animation
    """
    def adjust_all(self, transformation):
        d = self.delegate
        d.packing_trans[0] = d.packing_trans[0].dot(np.array(transformation, dtype='complex'))
        self.delegate.graphics.draw()

    def animate_all(self, transformation):
        # Create a new Animation Thread.  The new thread will insure our UI does not freeze.
        # The Animation Thread time is in milliseconds
        th = AnimationThread(self, transformation, 500)
        th.start()
        # th2 = AnimationThread(self, self.delegate.circles, transformation, 1000, len(self.delegate.circles) // 2,
        #                       len(self.delegate.circles))
        # th2.start()
        # The trigger is required when updating the circles every frame
        self.draw_trigger.connect(self.delegate.graphics.draw)

"""
The AnimationThread class animates transformations smoothly.

note that `self.parent().draw_trigger.emit()` is what updates the graphics
"""

class AnimationThread(QThread):

    def __init__(self, parent, transformation, tmill):
        super().__init__(parent)
        self.FPS = 48

        self.c_trans = parent.delegate.packing_trans
        self.orig_trans = np.copy(self.c_trans[0])
        self.trans = transformation
        self.time = tmill

        self.step = (np.array(self.trans, dtype='complex') - np.array(((1, 0), (0, 1)), dtype='complex'))

    
    def run(self):
        wait = 1000//self.FPS
        counter = 0

        while int(self.time/1000.0 * self.FPS) >= counter:
            #before = time.time()
            T = np.array(((1, 0), (0, 1)), dtype='complex') + self.step * swift_in_out(counter/(self.time/1000.0 * self.FPS))

            self.c_trans[0] = self.orig_trans.dot(T)
            # print(T, self.c_trans)
            # print("Circle Calculation time: %s ms" % int(1000*(time.time()-before)))
            # wait_time = wait - int(1000*(time.time()-before))

            self.parent().draw_trigger.emit()
            self.msleep(wait)
            counter += 1

        # update the last frame
        self.c_trans[0] = self.orig_trans.dot(np.array(self.trans, dtype='complex'))

        self.parent().draw_trigger.emit()
