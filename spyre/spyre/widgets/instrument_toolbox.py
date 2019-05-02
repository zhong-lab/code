from PyQt5 import QtWidgets, QtCore

from ..instrument import DictFeatItem, FeatItem
from .instrument_widget import DictFeatItemWidget, FeatItemWidget, ActionItemWidget

class InstrumentToolbox(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.instr_thread = QtCore.QThread()
        self.instr_thread.start()

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(['Feat', 'value'])

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.instruments = list()
        return

    def add_instrument(self, instr):
        instr.moveToThread(self.instr_thread)
        feats = instr.get_feats()
        actions = instr.get_actions()

        # Add a new instrument entry
        tree_item = QtWidgets.QTreeWidgetItem(0)
        self.tree.addTopLevelItem(tree_item)
        resource_items = len(instr.resource)
        resource = ''
        if resource_items == 1:
            resource = str(instr.resource[0])
        elif resource_items >= 2:
            resource = ', '.join(str(r) for r in instr.resource)
        name = instr._driver.split('.')[-1]
        if instr.alias:
            name = instr.alias + ' - ' + name
        self.tree.setItemWidget(tree_item, 0, QtWidgets.QLabel(name))
        tree_item.setText(1, resource)
        tree_item.setTextAlignment(1, QtCore.Qt.AlignRight)

        # Add all the feats to that intrument
        for feat_name, feat in sorted(feats.items()):
            feat.moveToThread(self.instr_thread)
            try:
                if isinstance(feat, DictFeatItem):
                    w = DictFeatItemWidget(feat)
                elif isinstance(feat, FeatItem):
                    w = FeatItemWidget(feat)
                else:
                    continue
            except Exception as e:
                w = QtWidgets.QPushButton()
                w.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning))
                w.setEnabled(False)
                w.setToolTip(str(e))
            label = QtWidgets.QLabel(feat_name)
            feat_item = QtWidgets.QTreeWidgetItem(1)
            tree_item.addChild(feat_item)
            self.tree.setItemWidget(feat_item, 0, label)
            self.tree.setItemWidget(feat_item, 1, w)

        # Add the actions
        for action_name, action in sorted(actions.items()):
            w = ActionItemWidget(action)
            label = QtWidgets.QLabel(action_name)
            action_item = QtWidgets.QTreeWidgetItem(2)
            tree_item.addChild(action_item)
            self.tree.setItemWidget(action_item, 0, label)
            self.tree.setItemWidget(action_item, 1, w)

        self.instruments.append(instr)
        return


class InstrumentTree(QtWidgets.QTreeView):

    pass

class InstrumentItem(object):

    def __init__(self, data, parent=None):
        self.parent = parent
        self._data = data
        self.children = list()
        return

    def appendChild(self, item):
        self.children.append(item)
        return

    def childCount(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def columnCount(self):
        return len(self._data)

    def data(self, column):
        return self._data[column]

    def row(self):
        if self.parent is not None:
            return self.parent.children.index(self)
        else:
            return 0

    def parentItem(self):
        return self.parent

class InstrumentTreeModel(QtCore.QAbstractItemModel):

    def __init__(self, data, parent=None):
        super().__init__(parent=parent)
        self.root_data = ['Key', 'Value']
        self.root = InstrumentItem(self.root_data)
        self.init_model(data)
        return

    def init_model(self, data):
        for key, value in sorted(data.items()):
            item = InstrumentItem([key, value])
            self.root.appendChild(item)
        for index in range(self.root.childCount()):
            child = self.root.child(index)
            print(child.data(0))
        return

    def index(self, row, column, parent):
        if self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        parent_item = parent.internalPointer() if parent.isValid() else self.root
        child_item = parent_item.child(row)
        index = self.createIndex(row, column, child_item) if child_item else QtCore.QModelIndex()
        return index

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()
        child_item = index.internalPointer()
        parent_item = child_item.parent
        if parent == self.root:
            return QtCore.QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0
        parent_item = parent.internalPointer() if parent.isValid() else self.root
        return parent_item.childCount()

    def columnCount(self, parent):
        parent_item = parent.internalPointer() if parent.isValid() else self.root
        return parent_item.columnCount()

    def data(self, index, role):
        print(index)
        if not index.isValid():
            return None
        if role != QtCore.Qt.DisplayRole:
            return None
        item = index.internalPointer()
        return item.data(index.column())

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return super().flags(index)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.root.data(section)
        return None

def main():
    data = {
        '1': 'testing 1',
        '2': 'testing 2',
        '3': 'testing 3',
    }
    app = QtWidgets.QApplication([])
    tree = QtWidgets.QTreeView()
    model = InstrumentTreeModel(data)
    tree.setModel(model)
    tree.show()
    app.exec_()

if __name__ == '__main__':
    main()
