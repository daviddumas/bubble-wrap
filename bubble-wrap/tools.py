"""
tools.py
"""

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from canvas3d import circular_torus_of_revolution
import datetime
import mobius
import numpy as np


# >>> UI Helpers <<<
def showListDialog(parent, ordered_dictionary, title):
    """
    Show a dropdown Dialog to select some item
    :param parent:
    :param ordered_dictionary: ordered dictionary of items to display
    :param title: window title
    :return:
    """
    model = QStandardItemModel(parent)

    for k in ordered_dictionary:
        item = QStandardItem(k)
        print(item.text())
        model.appendRow(item)

    response = [-1]

    dialog = QDialog(parent)
    uic.loadUi("ui/list_dialog.ui", dialog)
    dialog.setWindowTitle(title)
    dialog.listView.setModel(model)
    selectModel = dialog.listView.selectionModel()

    def getItem():
        response[0] = str(model.itemFromIndex(selectModel.currentIndex()).text())
        dialog.close()

    dialog.openBtn.clicked.connect(getItem)
    dialog.exec_()
    return response[0]


def showDropdownDialog(parent, items, title):
    """
    Show a dropdown Dialog to select some item
    :param parent:
    :param items: tuple of strings to display
    :param title: window title
    :return:
    """
    model = QStandardItemModel(parent)

    for k in items:
        item = QStandardItem(k)
        print(item.text())
        model.appendRow(item)

    response = [-1]

    dialog = QDialog(parent)
    uic.loadUi("ui/dropdown_dialog.ui", dialog)
    dialog.setWindowTitle(title)

    com = QComboBox()

    com.currentIndex()

    dialog.comboBox.setModel(model)

    def getItem():
        response[0] = dialog.comboBox.currentIndex()
        dialog.close()

    def cancelItem():
        dialog.close()

    dialog.openBtn.clicked.connect(getItem)
    dialog.cancelBtn.clicked.connect(cancelItem)
    dialog.exec_()
    return response[0]


def showProgressDialog(parent, progress_data, title="Loading..."):
    """
    Show a progress Dialog to select some item
    :param progress_data: list of [progress, is_still_working]
    :param title: window title
    :return:
    """

    class ProgressThread(QThread):
        def __init__(self, parent, progress_data):
            super().__init__(parent)

            self.pData = progress_data

        def run(self):
            while self.pData[1]:

                self.msleep(200)


    class ProgressQDialog(QDialog):

        def __init__(self, flags, *args, **kwargs):
            super().__init__(flags, *args, **kwargs)
            self.progress_bar = None

        def update_progress(self, frac):
            if self.progress_bar is not None:
                self.progress_bar.value(int(frac*100))

    dialog = ProgressQDialog(parent)
    uic.loadUi("ui/progress_dialog.ui", dialog)
    dialog.setWindowTitle(title)
    dialog.progress_bar = dialog.progressBar

    dialog.exec_()


class UnifiedEmbeddedCirclePacking:
    def __init__(self):
        self.opened_metadata = {}
        self.reset_metadata()
        self.opened_dcel = circular_torus_of_revolution(4, 4, rmaj=1, rmin=0.5)
        self.circles = []
        self.circles_optimize = [[]]
        self.dual_graph = False
        self.packing_trans = [np.array(((1, 0), (0, 1)), dtype='complex')]

        self.progressValue = [0]

    def reset_metadata(self):
        self.opened_metadata = {"schema_version": "0.2", "schema": "cpj",
                                           "timestamp": datetime.datetime.utcnow().isoformat() + 'Z'}

# >>> Threading Tools used for Enhanced Performance <<<
class OptimizeCirclesThread(QThread):
    def __init__(self, parent, circles, out_circles, mobius_transform=None, display_params=None):
        super().__init__(parent)

        self.C = circles
        self.OC = out_circles
        self.T = mobius_transform
        self.P = display_params
        self.cancel = False

    def run(self):
        zoom = self.P["zoom"]
        offset = self.P["pos"].copy()
        center = (self.P["center"][0], self.P["center"][1])
        width = self.P["width"]
        height = self.P["height"]

        outCir = []
        # transform circles
        m_circles = []
        T = mobius.make_sl2(self.T)
        for ci in self.C:
            if self.cancel:
                return
            m_circles.append((ci[0].transform_sl2(T), ci[1], ci[2]))

        dgraphcount = 0
        for i, c in enumerate(m_circles):
            if self.cancel:
                return

            cir = c[0]
            v = c[1]
            dualgraph_part = c[2]

            if dualgraph_part:
                dgraphcount += 1

            if not cir.contains_infinity and np.abs(zoom * cir.radius) > 1:
                # margin_threshold (change this parameter to allow more/less circles to be included off frame)
                mt = 50

                lc = center[0] + offset[0] + zoom * (cir.center.real - cir.radius)
                tc = center[1] + offset[1] + zoom * (cir.center.imag - cir.radius)
                dia = zoom * (cir.radius * 2)

                if lc < width + mt and lc + dia > -mt and tc < height + mt and tc + dia > -mt and dia > 2 or dualgraph_part:
                    outCir.append([self.C[i][0], v, dualgraph_part])

            elif cir.contains_infinity or dualgraph_part:
                outCir.append([self.C[i][0], v, dualgraph_part])

            if i % 50 == 0:
                self.parent().delegate.uecp.progressValue[0] = 100 * (i+1) / len(m_circles)
                self.parent().draw_trigger.emit()

        self.OC[0] = outCir.copy()
        self.parent().delegate.uecp.progressValue[0] = 100
        print("Done! Optimized %d circles." % len(self.OC[0]), "d-graph:", dgraphcount)
        self.parent().draw_trigger.emit()