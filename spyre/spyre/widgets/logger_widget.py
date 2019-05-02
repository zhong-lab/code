import logging
import time
import traceback as tb
from PyQt5 import QtWidgets, QtCore, QtGui

class LogWidget(QtWidgets.QWidget):

    entry_added = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.init_ui()
        return

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        log_table = QtWidgets.QTableWidget()
        log_table.setColumnCount(4)
        log_table.setHorizontalHeaderLabels(['Time', 'Type', 'Task', 'Message'])
        log_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        log_table.verticalHeader().setDefaultSectionSize(log_table.verticalHeader().minimumSectionSize())
        log_table.verticalHeader().hide()
        log_table.horizontalHeader().setStretchLastSection(True)
        log_table.itemSelectionChanged.connect(self.update_selection)
        self.log_table = log_table

        self.traceback_viewer = QtWidgets.QTextEdit()
        self.traceback_viewer.setReadOnly(True)
        self.traceback_viewer.setCurrentFont(QtGui.QFont("Consolas", 8))
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.log_table)
        splitter.addWidget(self.traceback_viewer)
        layout.addWidget(splitter)
        self.setLayout(layout)
        return

    def handler(self, exctype, value, traceback):
        row_position = self.log_table.rowCount()
        self.log_table.insertRow(row_position)
        self.entry_added.emit()

        now = time.strftime('%H:%M:%S %b %d, %Y', time.localtime(time.time()))

        typ = str(exctype.__name__)
        task = None
        exc_value = value

        item_strs = [now, typ, task, exc_value]
        for column, item_str in enumerate(item_strs):
            item = QtWidgets.QTableWidgetItem(str(item_str))
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            if column == 0:
                tb_text = ''.join(tb.format_exception(exctype, value, traceback)).strip()
                item.setData(QtCore.Qt.UserRole, tb_text)
            self.log_table.setItem(row_position, column, item)

        self.log_table.scrollToBottom()
        return

    def update_selection(self):
        items = self.log_table.selectedItems()
        if not items:
            return
        tb_text = items[0].data(QtCore.Qt.UserRole)
        self.traceback_viewer.setText(tb_text)
        return


class Logger(logging.Handler):

    def __init__(self, parent=None):
        super().__init__()
        self.widget = QtWidgets.QTextEdit(parent=parent)
        self.widget.setReadOnly(True)
        self.widget.setFontFamily('Consolas')
        self.widget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.widget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        return

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)
        return

class LoggerWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.logger = Logger(self)
        self.logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self.logger)
        logging.getLogger().setLevel(logging.DEBUG)

        self.init_ui()
        return

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.logger.widget)
        self.test_button = QtWidgets.QPushButton('Test')
        layout.addWidget(self.test_button)
        self.test_button.clicked.connect(self.test)
        self.setLayout(layout)
        return

    def test(self):
        logging.debug('TESTING')
        return

def main():
    app = QtWidgets.QApplication([])
    log = LogWidget()
    log.show()
    timer = QtCore.QTimer()
    iteration = 0
    def update():
        nonlocal iteration
        log.add_entry('iteration {}'.format(iteration))
        iteration += 1
        return

    timer.timeout.connect(update)
    timer.start(100)
    app.exec_()
    return

if __name__ == '__main__':
    main()
