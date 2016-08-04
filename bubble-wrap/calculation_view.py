import numpy as np
from PyQt5.QtCore import *

from interpolators import *
import openpacking
import solvepacking


class ControlCalculations(QObject):
    """
    Calculations controller attached to main delegate
    """
    # This trigger will be used to update the graphics every frame.
    draw_trigger = pyqtSignal()

    def __init__(self, d):
        super().__init__(parent=d)
        self.delegate = d
        # thread instances
        self.th_m = None
        self.th_a = None

        # set unified embedded circle packing holder
        self.uecp = self.delegate.uecp

        # Bind the buttons from the UI (identifier names specified in *.ui file)
        self.bind_button(d.invert_pack_btn)
        self.bind_button(d.solve_btn)
        self.bind_button(d.select_packing)

        self.draw_trigger.connect(self.delegate.graphics.draw)

    def bind_button(self, btn):
        # connects buttons to code
        btn.clicked.connect(lambda: self.btn_clicked(btn))

    def btn_clicked(self, btn):
        """
        Perform actions to button clicks
        :param btn:
        :return: void
        """
        d = self.delegate
        if btn == d.select_packing:
            # opens packings from dropdown menu if a file contains more than one packing
            if d.select_packing_dropdown.model().rowCount() > 0:
                loc = d.select_packing_dropdown.currentIndex()
                openpacking.from_select_packing(self, self.delegate, loc, lambda:self.delegate.graphics.draw())

        elif btn == d.invert_pack_btn:
            self.animate_all(np.array([[0, 1j], [1j, 0]]))

        elif btn == d.solve_btn:
            if self.uecp.opened_metadata is not None and float(self.uecp.opened_metadata["schema_version"]) >= 0.2 and self.uecp.opened_dcel is not None:
                solvepacking.from_torus_and_save(d.uecp.opened_dcel, fn='output/torus/torus.cpz')
            else:
                print("There is no surface to solve.")

    # >>> The following methods apply either an transformation adjustment or animation <<<
    def animate_all(self, transformation):
        """
        Mobius Transformation (with animation)
        :param transformation:
        :return:
        """
        # Create a new Animation Thread.  The new thread will insure our UI does not freeze.
        # The Animation Thread time is in milliseconds
        if self.th_m is None or self.th_m.isFinished():
            self.th_m = MobiusAnimationThread(self, transformation, 500)
            self.th_m.start()

    def animate_attributes(self, attr_obj, changes):
        """
        Attribute Transformation (with animation)
        :param attr_obj:
        :param changes:
        :return:
        """
        if self.th_a is None or self.th_a.isFinished():
            self.th_a = AttributeAnimationThread(self, attr_obj, changes, 500)
            self.th_a.start()


class MobiusAnimationThread(QThread):
    """
    A Thread designed to animate Mobius transformations
    """

    def __init__(self, parent, transformation, tmill):
        super().__init__(parent)
        self.FPS = 48

        self.c_trans = parent.uecp.packing_trans
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
