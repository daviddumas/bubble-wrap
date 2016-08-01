import numpy as np
from PyQt5.QtCore import *

import circle as circle
import lsons as lsons
import mobius as mobius
import serialization as ser
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
    """
    Calculations controller attached to main delegate
    """
    # This trigger will be used to update the graphics every frame.
    draw_trigger = pyqtSignal()

    def __init__(self, d):
        super().__init__(parent=d)
        self.delegate = d

        # set unified embedded circle packing holder
        self.uecp = self.delegate.uecp

        # Bind the buttons from the UI (identifier names specified in *.ui file)
        self.bind_button(d.testbtn1)
        self.bind_button(d.invert_pack_btn)
        self.bind_button(d.testbtn3)
        self.bind_button(d.reset_trans_btn)
        self.bind_button(d.solve_btn)
        self.bind_button(d.mobius_trans)

    def bind_button(self, btn):
        # connects buttons to code
        btn.clicked.connect(lambda: self.btn_clicked(btn))

    def btn_clicked(self, btn):
        """
        Perform actions to button clicks
        :param btn:
        :return: void
        """
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

        elif btn == d.solve_btn:
            solve_circle_packing_from_torus(self.delegate.m_dcel)
        elif btn == d.mobius_trans:
            d.uecp.mobius_trans_mode = d.mobius_trans.isChecked()

    # >>> The following methods apply either an transformation adjustment or animation <<<
    def adjust_all(self, transformation):
        """
        Mobius Transformation (No animation)
        :param transformation:
        :return:
        """
        self.uecp.packing_trans[0] = self.uecp.packing_trans[0].dot(np.array(transformation, dtype='complex'))
        self.delegate.graphics.draw()

    def animate_all(self, transformation):
        """
        Mobius Transformation (with animation)
        :param transformation:
        :return:
        """
        # Create a new Animation Thread.  The new thread will insure our UI does not freeze.
        # The Animation Thread time is in milliseconds
        th = MobiusAnimationThread(self, transformation, 500)
        th.start()

        # The trigger is required when updating the circles every frame
        self.draw_trigger.connect(self.delegate.graphics.draw)

    def animate_attributes(self, attr_obj, changes):
        th = AttributeAnimationThread(self, attr_obj, changes, 500)
        th.start()

        # The trigger is required when updating the circles every frame
        self.draw_trigger.connect(self.delegate.graphics.draw)


class MobiusAnimationThread(QThread):
    """
    A Thread designed to animate Mobius transformations
    """

    def __init__(self, parent, transformation, tmill):
        super().__init__(parent)
        self.FPS = 48

        self.c_trans = self.delegate.uecp.packing_trans
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
        # No need to force optimization because a change in the mobius transformation will automatically
        # trigger it to re-optimize.
        # Tell the UI to redraw
        self.parent().draw_trigger.emit()


class AttributeAnimationThread(QThread):
    def __init__(self, parent, attr_obj, changes, tmill):
        """
        AttributeAnimationThread animates properties within a dictionary
        :param parent: parent QObject
        :param attr_obj: reference to dictionary object with floating point properties
        :param changes: a dictionary with final values
        :param tmill: time in milliseconds
        """
        super().__init__(parent)
        self.FPS = 30

        self.attr_obj = attr_obj
        self.orig_attr_obj = dict(attr_obj)
        self.attr_changes = changes
        self.time = tmill
        # a dictionary that holds each step for each parameter
        self.step = {}

        for k in self.attr_changes:
            if isinstance(self.attr_changes[k], list) or isinstance(self.attr_changes[k], tuple):
                self.orig_attr_obj[k] = self.orig_attr_obj[k].copy()
                self.step[k] = []
                for i, v in enumerate(self.attr_changes[k]):
                    self.step[k].append(v - self.attr_obj[k][i])

                print(self.attr_obj[k], self.attr_changes[k], self.step[k])
            else:
                self.step[k] = float(self.attr_changes[k] - self.attr_obj[k])

    def run(self):
        wait = 1000 // self.FPS
        counter = 0

        while int(self.time / 1000.0 * self.FPS) >= counter:
            # before = time.time()
            for k in self.step:
                if isinstance(self.step[k], list):
                    for i, v in enumerate(self.step[k]):
                        T = self.step[k][i] * swift_in_out(counter / (self.time / 1000.0 * self.FPS))
                        self.attr_obj[k][i] = self.orig_attr_obj[k][i] + T
                else:
                    T = self.step[k] * swift_in_out(counter / (self.time / 1000.0 * self.FPS))
                    self.attr_obj[k] = self.orig_attr_obj[k] + T

            self.parent().draw_trigger.emit()
            self.msleep(wait)
            counter += 1

        # update the last frame
        for k in self.attr_changes:
            self.attr_obj[k] = self.attr_changes[k]

        # Force update will require the UI to optimize the circle packing for snappy interaction
        self.parent().delegate.graphics.force_update()
        # Tell the UI to redraw
        self.parent().draw_trigger.emit()
