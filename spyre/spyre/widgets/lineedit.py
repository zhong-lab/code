from PyQt5 import QtWidgets, QtCore

class LineEdit(QtWidgets.QLineEdit):

    activated = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        go_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DialogOkButton)
        activated_action = self.addAction(go_icon, QtWidgets.QLineEdit.TrailingPosition)
        activated_action.triggered.connect(lambda: self.activated.emit(self.text()))
        return
