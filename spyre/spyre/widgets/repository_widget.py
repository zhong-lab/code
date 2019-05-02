from PyQt5 import QtWidgets
from spyre.repository import Repository, Node
from spyre.plotting import BasePlotWidget
import time

class RepositoryWidget(QtWidgets.QWidget):

    def __init__(self, spyrelet, parent=None):
        super().__init__(parent=parent)
        self.spyrelet = spyrelet
        self.filename = None
        self.repo = None
        self.init_ui()
        return

    def init_ui(self):
        # Create file selection widget
        file_w = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        file_w.setLayout(layout)
        self.filename_label = QtWidgets.QLabel('Currently selected repository:')
        self.select_repository = QtWidgets.QPushButton('Select repository...')
        self.select_repository.clicked.connect(self.select_repository_dialog)
        layout.addWidget(self.select_repository)
        layout.addWidget(self.filename_label)

        # Entry widget
        entry_w = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout()
        entry_w.setLayout(layout)
        label = QtWidgets.QLabel('Entry name: ')
        self.dataset_name = QtWidgets.QLineEdit()
        layout.addWidget(label)
        layout.addWidget(self.dataset_name)
        self.dataset_name.setText(self.spyrelet.__class__.__name__)

        # Other widget
        self.dataset_description = QtWidgets.QTextEdit()
        self.save_btn = QtWidgets.QPushButton('Save')
        self.save_btn.clicked.connect(self.save)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(file_w)
        layout.addWidget(entry_w)
        layout.addWidget(QtWidgets.QLabel('Description:'))
        layout.addWidget(self.dataset_description)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)
        return

    def select_repository_dialog(self):
        filename, other = QtWidgets.QFileDialog.getSaveFileName(None, 'Save repository to...', '', 'HDF5 files (*.h5)')
        if filename:
            self.filename_label.setText('Currently selected repository: {}'.format(filename))
            self.filename = filename
            self.repo = Repository(filename)
        return

    def generate_plotdata_nodes(self):
        d = dict()
        for element_name in self.spyrelet.element_names:
            w = self.spyrelet.elements[element_name].widget
            if issubclass(w.__class__, BasePlotWidget):
                d[element_name] = w.generate_node(element_name)
        return d

    def generate_node(self, name_overwrite=None):
        # Note this can be modify for custom node generation when necessary
        uid = name_overwrite if not name_overwrite is None else 'uid{}'.format(self.repo.get_uid())
        node = Node(uid, dataframe = self.spyrelet.dataset.get_frame_copy())
        plot_nodes = self.generate_plotdata_nodes()
        for element_name in plot_nodes:
            node.add_node(node = plot_nodes[element_name])
        return node

    def save(self):
        if self.repo is None:
            raise Exception("No file as been chosen for the repository")
        description = self.dataset_description.toPlainText()
        node = self.generate_node()
        name = self.dataset_name.text()
        self.repo.add_entry(node=node, description=description, name=name, date=time.strftime('%Y-%m-%d'), time=time.strftime('%H:%M:%S'), spyrelet=str(self.spyrelet.__class__.__name__))
        self.repo.save()
        print('Data was saved! ({})'.format(node.name))
        return
