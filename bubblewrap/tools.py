"""
tools.py
"""

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def showListDialog(parent, ordered_dictionary):
    model = QStandardItemModel(parent)

    for k in ordered_dictionary:
        item = QStandardItem(k)
        print(item.text())
        model.appendRow(item)

    # qmi = QModelIndex()
    # qmi.row()
    response = [-1]



    dialog = QDialog(parent)
    uic.loadUi("ui/list_dialog.ui", dialog)
    dialog.listView.setModel(model)
    selectModel = dialog.listView.selectionModel()

    def getItem():
        response[0] = str(model.itemFromIndex(selectModel.currentIndex()).text())
        dialog.close()

    dialog.openBtn.clicked.connect(getItem)
    dialog.exec_()
    return response[0]