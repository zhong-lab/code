from PyQt5 import QtCore, QtGui, QtWidgets
import os

from .splitter_widget import Splitter, SplitterOrientation

from .task import TaskWidget

class TaskOverview(QtWidgets.QWidget):

    def __init__(self, tasks, parent=None):
        super().__init__(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.task_list = QtWidgets.QListWidget()
        self.task_list.setVerticalScrollMode(self.task_list.ScrollPerPixel)
        layout.addWidget(self.task_list)
        self.setLayout(layout)

        self.task_list.clear()
        for task_name, task in sorted(tasks.items()):
            task_widget = TaskWidget(task)
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(task_widget.sizeHint())
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsSelectable)

            self.task_list.addItem(item)
            self.task_list.setItemWidget(item, task_widget)
        return

class SpyreletWidget(QtWidgets.QWidget):

    def __init__(self, spyrelet, parent=None):
        super().__init__(parent=parent)
        self.spyrelet = spyrelet
        self.task_overview = TaskOverview(spyrelet.tasks)
        self.container = QtWidgets.QMdiArea()
        self.container.setBackground(QtGui.QBrush(QtGui.QColor(10, 10, 10)))
        self.count = 0
        for element_name, element in sorted(spyrelet.elements.items()):
            self.count += 1
            subwindow = SubWindow()
            w = element()
            internal_layout = QtWidgets.QVBoxLayout()
            internal_layout.addWidget(w)
            internal_layout.setContentsMargins(0, 0, 0, 0)
            internal_container = QtWidgets.QWidget()
            internal_container.setLayout(internal_layout)
            subwindow.setWidget(internal_container)
            subwindow.setWindowFlags(QtCore.Qt.CustomizeWindowHint | QtCore.Qt.Tool | QtCore.Qt.WindowTitleHint)
            subwindow.setWindowTitle(element_name)
            subwindow.button_build()
            subwindow.resize(w.minimumSizeHint())
            subwindow.setObjectName(element_name)
            self.container.addSubWindow(subwindow)

        layout = QtWidgets.QVBoxLayout(self)
        splitter_config = {
            'side_w': self.container,
            'main_w': self.task_overview,
            'orientation': SplitterOrientation.horizontal_bottom_button,
        }
        splitter = Splitter(**splitter_config)
        layout.addWidget(splitter)
        # layout.addWidget(self.task_overview)
        # layout.addWidget(self.container)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        return

    def save_elements_state(self):
        state = dict()
        for name in self.spyrelet.element_names:
            el_state = getattr(self.spyrelet, name).save_state()
            if not el_state is None:
                state[name] = el_state
        if len(state):
            return state
        else:
            return None

    def load_elements_state(self, state):
        for name in self.spyrelet.element_names:
            if name in state:
                getattr(self.spyrelet, name).load_state(state[name])

class SubWindow(QtWidgets.QMdiSubWindow):
    state_change = QtCore.pyqtSignal()
    def __init__(self):
        QtWidgets.QMdiSubWindow.__init__(self)
        image_path = os.path.join(os.path.dirname(__file__),'..\\images\\')
        image_path = os.path.normpath(image_path)
        image_path = image_path.replace("\\","/")
        btn_style =  """background-image: url('{}/{}');
                                    border-color: rgb(65,65,65);
                                    border-style: outset;
                                    border-width: 1px;
                                    border-radius: 3px;
                                """.format(image_path, '{}')

        self.min_inactive = btn_style.format("minimize.png")
        self.max_inactive = btn_style.format("maximize.png")
        self.restore_inactive = btn_style.format("restore.png")
        self.min_active = btn_style.format("minimize_blue.png")
        self.max_active = btn_style.format("maximize_blue.png")
        self.restore_active = btn_style.format("restore_blue.png")

        self.style_params = {
                        'normal_activated': (self.min_active, self.max_active),
                        'normal_deactivated': (self.min_inactive, self.max_inactive),
                        'minimized_activated': (self.restore_active, self.max_active),
                        'minimized_deactivated': (self.restore_inactive, self.max_inactive),
                        'maximized_activated': (self.min_active, self.restore_active),
        }

    def button_build(self):
        self.min_btn = QtWidgets.QToolButton(self)
        self.max_btn = QtWidgets.QToolButton(self)
        self.min_btn.setFixedSize(18, 18)
        self.max_btn.setFixedSize(18, 18)
        self.min_btn.move(self.width()-45, 3)
        self.max_btn.move(self.width()-25, 3)
        self.min_btn.clicked.connect(self.minimize)
        self.max_btn.clicked.connect(self.maximize)
        self.style('normal_activated')

    def style(self, window_state):
        styles = self.style_params[window_state]
        self.min_btn.setStyleSheet(styles[0])
        self.max_btn.setStyleSheet(styles[1])

    def minimize(self):
        if self.isMinimized():
            self.showNormal()
            self.style('normal_activated')
        else:
            self.showMinimized()
            self.style('minimized_activated')

    def maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.style('normal_activated')
        else:
            self.showMaximized()
            self.style('maximized_activated')

    def resizeEvent(self, event):
        self.min_btn.move(self.width()-45, 3)
        self.max_btn.move(self.width()-25, 3)
        QtWidgets.QMdiSubWindow.resizeEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        if event.y() > 0 and event.y() < 25:
            self.maximize()

    def changeEvent(self, event):
        if event.type() == 105:
            if self.isMaximized():
                self.style('maximized_activated')
            elif not self.isMinimized():
                self.style('normal_deactivated')
            elif self.isMinimized():
                self.style('minimized_deactivated')
        QtWidgets.QMdiSubWindow.changeEvent(self, event)

    def mousePressEvent(self, event):
        if not self.isMinimized() and not self.isMaximized():
            self.style('normal_activated')
        elif self.isMinimized():
            self.style('minimized_activated')
        QtWidgets.QMdiSubWindow.mousePressEvent(self, event)

    def closeEvent(self, event):
        event.ignore()
