import cmath
import time

import numpy as np
from PyQt5.QtCore import *

import cpps.circle as c
from canvas3d import Point3D, rotate_3d_points, orient_3d_points
from interpolators import *


class ControlCalculations(QObject):

    # This trigger will be used to update the graphics every frame.  At the moment it is arbitrary
    draw_trigger = pyqtSignal()

    def __init__(self, delegate):
        super().__init__(parent=delegate)
        self.delegate = delegate

        # Bind the buttons from the UI
        self.bind_btn(delegate.testbtn1)
        self.bind_btn(delegate.testbtn2)
        self.bind_btn(delegate.testbtn3)
        self.bind_btn(delegate.testbtn4)
        self.bind_btn(delegate.bigger_cir)
        delegate.amountSlider.valueChanged.connect(lambda: self.adjustCircles(int(delegate.amountSlider.value())))
        delegate.xrot.valueChanged.connect(lambda: self.adjustShape())
        delegate.yrot.valueChanged.connect(lambda: self.adjustShape())
        delegate.zrot.valueChanged.connect(lambda: self.adjustShape())
        delegate.bigger_cir_slider.valueChanged.connect(lambda: self.slide_test_circle())
        self.adjustCircles(9)


    def slide_test_circle(self):
        d = self.delegate
        d.testRad[0] = int(d.bigger_cir_slider.value())
        d.circle_rad.setText("Circle Radius: %d" % d.testRad[0])
        d.graphics.draw()

    def bind_btn(self, btn):
        btn.clicked.connect(lambda: self.btn_clicked(btn))

    def adjustCircles(self, num_of_circles):
        side = int(math.sqrt(num_of_circles))
        scale = 1/side
        # Bind Data Structures
        self.delegate.circles = [c.from_center_radius(
            complex(x * scale, cmath.sqrt(3) * scale/2 * y) if y % 2 == 0 else complex(x * scale + scale/2, cmath.sqrt(3) * scale/2 * y), scale/2)
                        for x in range(-side//2, side//2+1) for y in range(-side//2, side//2+1)]
        self.delegate.num_of_circles_label.setText("Number of circles: %d" % int((side+1)**2))
        self.delegate.graphics.draw()

    def adjustShape(self):
        orient_3d_points(self.delegate.points, Point3D(float(self.delegate.xrot.value())/100,
                                                       float(self.delegate.yrot.value())/100,
                                                       float(self.delegate.zrot.value())/100), around_point3d=Point3D(0,0,0))
        self.delegate.graphics.draw()

    def btn_clicked(self, btn):
        T = ((1.005 + 1.005j, 0.01),
             (0.5, 1 + 0.5j))

        d = self.delegate
        if btn == d.testbtn1:
            self.adjust_all(T)
        elif btn == d.testbtn2:
            self.adjust_all(np.linalg.inv(T))

        elif btn == d.testbtn3:
            self.animate_all(T)
        elif btn == d.testbtn4:
            self.animate_all(np.linalg.inv(T))

        elif btn == d.bigger_cir:
            d.testRad[0] = d.testRad[0]**2
            d.circle_rad.setText("Circle Radius: %d" % d.testRad[0])
            d.graphics.draw()


    """
    The following methods apply either an transformation adjustment or animation
    """
    def adjust_all(self, transformation):
        d = self.delegate
        for i in range(len(d.circles)):
            d.circles[i] = d.circles[i].transform_gl2(transformation)
        self.delegate.graphics.draw()

    def animate_all(self, transformation):
        # Create a new Animation Thread.  The new thread will insure our UI does not freeze.
        # The Animation Thread time is in milliseconds
        th = AnimationThread(self, self.delegate.circles, transformation, 500, 0, len(self.delegate.circles), self.delegate.points)
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

    def __init__(self, parent, circles, transformation, tmill, start_i, end_i, points):
        super().__init__(parent)
        self.FPS = 48

        self.orig_circles = circles.copy()
        self.circles = circles
        self.trans = transformation
        self.time = tmill
        self.s_i = start_i
        self.e_i = end_i
        self.points = points

        self.step = (np.array(self.trans, dtype='complex') - np.array(((1, 0), (0, 1)), dtype='complex'))

    
    def run(self):
        wait = 1000//self.FPS
        counter = 0

        rotate_amount = math.pi / 2 / (self.time/1000.0 * self.FPS)

        while int(self.time/1000.0 * self.FPS) >= counter:
            before = time.time()
            T = np.array(((1, 0), (0, 1)), dtype='complex') + self.step * swift_in_out(counter/(self.time/1000.0 * self.FPS))

            T = T / np.sqrt(np.linalg.det(T))

            for ci in range(self.s_i, self.e_i):
                self.circles[ci] = self.orig_circles[ci].transform_sl2(T)

            print("Circle Calculation time: %s ms" % int(1000*(time.time()-before)))
            # wait_time = wait - int(1000*(time.time()-before))

            rotate_3d_points(self.points, Point3D(-rotate_amount/2, rotate_amount/2, rotate_amount), Point3D(0,0,0))
            #print(self.points[0])

            self.parent().draw_trigger.emit()
            self.msleep(wait)
            counter += 1


        # update the last frame
        for ci in range(len(self.circles)):
            self.circles[ci] = self.orig_circles[ci].transform_gl2(np.array(self.trans))

        self.parent().draw_trigger.emit()
