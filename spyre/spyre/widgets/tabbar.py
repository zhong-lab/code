from PyQt5 import QtWidgets, QtCore

class TabBar(QtWidgets.QTabBar):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.tabBarDoubleClicked.connect(self.begin_editing)
        self.editor = None
        return

    def begin_editing(self, index):
        print('begin edit')
        if index < 0:
            return
        self.edit_index = index
        self.editor = QtWidgets.QLineEdit()
        self.editor.focusOutEvent = self.editorFocusOutEvent
        self.editor.setParent(self)
        self.editor.show()
        self.editor.setFocus()
        self.editor.editingFinished.connect(lambda: self.finish_editing())
        self.editor.setText(self.tabText(index))
        self.editor.selectAll()

        rect = self.tabRect(index)
        self.editor.setGeometry(rect)
        return

    def finish_editing(self):
        print('finish edit')
        new_tab_name = self.editor.text()
        if new_tab_name:
            self.setTabText(self.currentIndex(), new_tab_name)
        self.editor.hide()
        return

    def editorFocusOutEvent(self, ev):
        self.finish_editing()
        super().focusOutEvent(ev)
        return





class TabWidget(QtWidgets.QTabWidget):

    def __init__(self, default_tab_w, default_name, parent=None):
        super().__init__(parent=parent)
        self.default_tab_w = default_tab_w
        self.default_name = default_name
        self.tab = TabBar()
        self.setTabBar(self.tab)
        self.tabButton = QtWidgets.QToolButton(self)
        self.tabButton.setText('+')
        font = self.tabButton.font()
        font.setBold(True)
        self.tabButton.setFont(font)
        self.setCornerWidget(self.tabButton)
        self.tabButton.clicked.connect(self.add_default_tab)

        self.setMovable(True)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid black;
                background: white;
            }

            QTabWidget::tab-bar:top {
                top: 1px;
            }

            QTabWidget::tab-bar:bottom {
                bottom: 1px;
            }

            QTabWidget::tab-bar:left {
                right: 1px;
            }

            QTabWidget::tab-bar:right {
                left: 1px;
            }

            QTabBar::tab {
                border: 1px solid black;
            }

            QTabBar::tab:selected {
                background: white;
            }

            QTabBar::tab:!selected {
                background: silver;
            }

            QTabBar::tab:!selected:hover {
                background: #999;
            }

            QTabBar::tab:top:!selected {
                margin-top: 3px;
            }

            QTabBar::tab:bottom:!selected {
                margin-bottom: 3px;
            }

            QTabBar::tab:top, QTabBar::tab:bottom {
                min-width: 8ex;
                margin-right: -1px;
                padding: 5px 10px 5px 10px;
            }

            QTabBar::tab:top:selected {
                border-bottom-color: none;
            }

            QTabBar::tab:bottom:selected {
                border-top-color: none;
            }

            QTabBar::tab:top:last, QTabBar::tab:bottom:last,
            QTabBar::tab:top:only-one, QTabBar::tab:bottom:only-one {
                margin-right: 0;
            }

            QTabBar::tab:left:!selected {
                margin-right: 3px;
            }

            QTabBar::tab:right:!selected {
                margin-left: 3px;
            }

            QTabBar::tab:left, QTabBar::tab:right {
                min-height: 8ex;
                margin-bottom: -1px;
                padding: 10px 5px 10px 5px;
            }

            QTabBar::tab:left:selected {
                border-left-color: none;
            }

            QTabBar::tab:right:selected {
                border-right-color: none;
            }

            QTabBar::tab:left:last, QTabBar::tab:right:last,
            QTabBar::tab:left:only-one, QTabBar::tab:right:only-one {
                margin-bottom: 0;
            }"""
        )
        return

    def add_default_tab(self):
        w = self.default_tab_w()
        self.addTab(w, self.default_name)
        return

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    tw = TabWidget(lambda: QtWidgets.QPushButton('test'), 'test button')
    tw.addTab(QtWidgets.QPushButton('test'), 'test button')
    tw.resize(600, 600)
    tw.show()
    app.exec_()
