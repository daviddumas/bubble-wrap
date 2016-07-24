"""
tools.py
"""

from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


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
