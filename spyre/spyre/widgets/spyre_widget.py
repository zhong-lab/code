from PyQt5 import QtCore, QtGui, QtWidgets
import importlib.util
import inspect
import pydoc

from lantz.driver import Driver
from ..spyrelet import Spyrelet
from ..task import TaskWrapper
from .tabbar import TabBar
from .instrument_toolbox import InstrumentToolbox
from .console_widget import Console
from .logger_widget import LogWidget
from .splitter_widget import Splitter, SplitterOrientation
from .lineedit import LineEdit

from ..persist import Persister

class FileSelectionLineEdit(QtWidgets.QLineEdit):

    file_selected = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        args = [
            self.style().standardIcon(QtWidgets.QStyle.SP_DialogOpenButton),
            QtWidgets.QLineEdit.TrailingPosition,
        ]
        action = self.addAction(*args)
        action.triggered.connect(self.select_file)
        return

    def select_file(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName()
        self.setText(filename)
        self.file_selected.emit(filename)
        return

class AddInstrumentWizard(QtWidgets.QWizard):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle('Add instrument')
        self.setWizardStyle(QtWidgets.QWizard.ModernStyle)
        self.driver_class_path = LineEdit()
        self.driver_class_path.activated.connect(self.on_path_selected)
        self.outer_container = QtWidgets.QWidget()
        self.driver_init_params = QtWidgets.QTableWidget()
        self.driver_init_params.setColumnCount(2)
        self.driver_init_params.setHorizontalHeaderLabels(['Name', 'Value'])
        self.driver_init_params.horizontalHeader().setStretchLastSection(True)
        self.driver_init_params.verticalHeader().setDefaultSectionSize(self.driver_init_params.verticalHeader().minimumSectionSize())
        self.driver_init_params.verticalHeader().hide()
        self.init_page()
        return

    def init_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle('Select instrument to add...')
        layout = QtWidgets.QFormLayout()
        layout.addRow('Instrument path', self.driver_class_path)
        layout.addRow('Initialization parameters', self.driver_init_params)
        page.setLayout(layout)
        self.addPage(page)
        return

    def on_path_selected(self, path):
        driver_class = pydoc.locate(path)
        if driver_class is None:
            print('Could not find specified class path')
            return
        try:
            islantzdriver = issubclass(driver_class, Driver)
        except TypeError:
            print('Did not receive class type')
        if not islantzdriver:
            print('Not a valid lantz driver')
            return
        sig = inspect.signature(driver_class.__init__)
        self.driver_init_params.setRowCount(0)
        idx = 0
        for name, param in list(sig.parameters.items())[1:]:
            if param.kind == param.POSITIONAL_ONLY or param.kind == param.POSITIONAL_OR_KEYWORD:
                self.driver_init_params.insertRow(self.driver_init_params.rowCount())
                name_item = QtWidgets.QTableWidgetItem(name)
                value_item = QtWidgets.QLineEdit()
                value_item.setText(str(param.default) if param.default != param.empty else '')
                self.driver_init_params.setItem(idx, 0, name_item)
                self.driver_init_params.setCellWidget(idx, 1, value_item)
                idx += 1
        return


class AddSpyreletWizard(QtWidgets.QWizard):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle('Add spyrelet')
        self.setWizardStyle(QtWidgets.QWizard.ModernStyle)
        self.file_path = FileSelectionLineEdit()
        self.file_path.file_selected.connect(self.on_file_selected)
        self.discovered_spyrelets = QtWidgets.QComboBox()
        self.req_instrument_selection = QtWidgets.QTableWidget()
        self.req_spyrelet_selection = QtWidgets.QTableWidget()
        self.init_page()
        return

    def init_page(self):
        page = QtWidgets.QWizardPage()
        page.setTitle('Select spyrelet to add...')
        layout = QtWidgets.QFormLayout()
        layout.addRow('Spyrelet path', self.file_path)
        layout.addRow('Spyrelets in file', self.discovered_spyrelets)
        layout.addRow('Required instruments', self.req_instrument_selection)
        layout.addRow('Required spyrelets', self.req_spyrelet_selection)
        page.setLayout(layout)
        self.addPage(page)
        return

    def on_file_selected(self, filename):
        spec = importlib.util.spec_from_file_location('*', filename)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.discovered_spyrelets.clear()
        for name, obj in sorted(inspect.getmembers(mod, inspect.isclass)):
            if issubclass(obj, Spyrelet) and obj != Spyrelet:
                self.discovered_spyrelets.addItem(name, obj)


        def spyrelet_selected(index):
            spyrelet = self.spyrelets_in_path.itemData(index)

            layout = self.spyrelet_instruments_layout
            for idx in reversed(range(layout.count())):
                item = layout.itemAt(idx)
                layout.removeItem(item)

            for instr_name, instr_class in spyrelet.requires.items():
                instr_shortname = repr(instr_class).split("'")[1].split('.')[-1]
                instr_selector = QtWidgets.QComboBox()
                layout.addRow("{} (class '{}')".format(instr_name, instr_shortname), instr_selector)
            # self.spyrelet_instruments.setLayout(layout)
            return
        return

class SpyreWidget(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle('Spyre')
        self.fullscreen = False
        self.prev_wintype = self.windowType()
        self.init_ui()

        self.persit_subpath = 'Spyre'

        return

    def init_ui(self):
        self.toolbox = QtWidgets.QToolBox()
        self.iw = InstrumentToolbox()
        self.toolbox.addItem(self.iw, 'Instruments')
        self.spyrelet_tabs = QtWidgets.QMainWindow()
        placeholder = QtWidgets.QWidget()
        self.spyrelet_tabs.setCentralWidget(placeholder)
        self.spyrelet_tabs.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks | QtWidgets.QMainWindow.AllowTabbedDocks)
        self.spyrelet_tabs.setTabPosition(QtCore.Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.North)

        self.console = Console()
        self.logger = LogWidget()
        self.debug = QtWidgets.QWidget()
        self.test_close = QtWidgets.QPushButton('Test Close')
        self.test_close.clicked.connect(self.save_spyrelet_geometries)
        self.test_restore = QtWidgets.QPushButton('Test Restore')
        self.test_restore.clicked.connect(self.restore_spyrelet_geometries)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.test_close)
        layout.addWidget(self.test_restore)
        self.debug.setLayout(layout)

        self.unread_entries = 0
        self.info_tab = QtWidgets.QTabWidget()
        self.info_tab.addTab(self.logger, 'Log')
        self.info_tab.addTab(self.console, 'Console')
        # self.info_tab.addTab(self.debug, 'Debug')
        self.info_tab.currentChanged.connect(self.reset_unread_entries)

        self.logger.entry_added.connect(self.update_info_tab)

        splitter_config = {
            'main_w': self.spyrelet_tabs,
            'side_w': self.info_tab,
            'orientation': SplitterOrientation.horizontal_top_button,
        }
        v_splitter = Splitter(**splitter_config)

        splitter_config = {
            'main_w': self.toolbox,
            'side_w': v_splitter,
            'orientation': SplitterOrientation.vertical_right_button,
        }
        h_splitter = Splitter(**splitter_config)
        # v_splitter.setSizes([400, 1])
        # h_splitter.setSizes([1, 400])
        v_splitter.setHandleWidth(10)
        h_splitter.setHandleWidth(10)

        menubar = self.menuBar()
        add_menu = menubar.addMenu('Add')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(menubar)
        layout.addWidget(h_splitter)
        layout.setContentsMargins(0, 0, 0, 0)



        add_spyrelet_action = QtWidgets.QAction('Spyrelet', self)
        add_spyrelet_action.triggered.connect(self.add_spyrelet_dialog)

        add_instrument_action = QtWidgets.QAction('Instrument', self)
        add_instrument_action.triggered.connect(self.add_instrument_dialog)

        add_menu.addAction(add_spyrelet_action)
        add_menu.addAction(add_instrument_action)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        placeholder.hide()
        return

    def add_spyrelet_dialog(self):
        wizard = AddSpyreletWizard(self)
        wizard.exec_()
        return

    def add_instrument_dialog(self):
        wizard = AddInstrumentWizard(self)
        wizard.exec_()
        return

    def update_info_tab(self, force=False, new_entries=1):
        if self.info_tab.currentIndex() != 0 or force:
            self.unread_entries += new_entries
            log_tab_text = 'Log' if not self.unread_entries else 'Log ({})'.format(self.unread_entries)
            self.info_tab.setTabText(0, log_tab_text)
        return

    def reset_unread_entries(self):
        self.unread_entries = 0
        self.update_info_tab(force=True, new_entries=0)
        return

    def spyrelet_added_handler(self, spyrelet_widget, name):
        dock = QtWidgets.QDockWidget(name)
        dock.setObjectName(name)
        dock.setWidget(spyrelet_widget)
        spyrelet_widget.setParent(dock)
        dock.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        dock.setAllowedAreas(QtCore.Qt.DockWidgetArea(2))

        dock_title = QtWidgets.QLabel(name, dock)
        dock_title.setStyleSheet(
        """
            background-color: rgb(20, 20, 20);
            color: white;
            font-size: 8pt;
            padding: 5px;
        """
        )
        dock.setTitleBarWidget(dock_title)
        existing_dockwidgets = self.spyrelet_tabs.findChildren(QtWidgets.QDockWidget)
        self.spyrelet_tabs.addDockWidget(QtCore.Qt.DockWidgetArea(2), dock)
        if existing_dockwidgets:
            self.spyrelet_tabs.tabifyDockWidget(existing_dockwidgets[-1], dock)
        return

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_F11:
            if self.fullscreen:
                self.setWindowFlags(self.prev_wintype)
                self.showMaximized()
                self.fullscreen = False
            else:
                self.prev_wintype = self.windowType()
                self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
                self.showFullScreen()
                self.fullscreen = True
        elif e.key() == QtCore.Qt.Key_Alt:
            self.menuBar().setHidden(not self.menuBar().isHidden())
        return

    def save_spyrelet_geometries(self):
        dockwidgets = self.spyrelet_tabs.findChildren(QtWidgets.QDockWidget)
        dock_geom = self.spyrelet_tabs.saveState()
        spyrelets = dict()
        spyrelets_elements = dict()
        for spyreletw_dockwidget in dockwidgets:
            spyreletw = spyreletw_dockwidget.widget()
            spyrelet = spyreletw.spyrelet
            s_name = spyreletw_dockwidget.objectName()
            spyrelet_path = '.'.join((spyrelet.__class__.__module__, spyrelet.__class__.__qualname__))
            element_subwindows = spyreletw.container.subWindowList()
            element_geometries = dict()
            for element_subwindow in element_subwindows:
                element_layout = element_subwindow.widget().layout()
                element = element_layout.itemAt(0).widget()
                element_name = element_subwindow.objectName()
                element_geom = element_subwindow.saveGeometry()
                element_geometries[element_name] = element_geom
            spyrelets[s_name] = element_geometries

            #Save state of elements
            elements_state = spyreletw.save_elements_state()
            if not elements_state is None:
                spyrelets_elements[s_name] = elements_state

        p = Persister(subpath_name=self.persit_subpath)
        p.dump_spyrelets(dock_geom, spyrelets, spyrelets_elements)
        return

    def restore_spyrelet_geometries(self):
        p = Persister(subpath_name=self.persit_subpath)
        try:
            dock_geom, spyrelets, spyrelets_elements = p.load_spyrelets()
        except KeyError:
            return
        self.spyrelet_tabs.restoreState(dock_geom)
        dockwidgets = self.spyrelet_tabs.findChildren(QtWidgets.QDockWidget)
        for spyreletw_dockwidget in dockwidgets:
            spyreletw = spyreletw_dockwidget.widget()
            spyrelet = spyreletw.spyrelet
            s_name = spyreletw_dockwidget.objectName()
            spyrelet_path = '.'.join((spyrelet.__class__.__module__, spyrelet.__class__.__qualname__))
            sw_name = spyreletw_dockwidget.objectName()
            if sw_name in spyrelets:
                element_geometries = spyrelets[sw_name]
                element_subwindows = spyreletw.container.subWindowList()
                for element_subwindow in element_subwindows:
                    element_layout = element_subwindow.widget().layout()
                    element = element_layout.itemAt(0).widget()
                    el_name = element_subwindow.objectName()
                    if el_name in element_geometries:
                        element_subwindow.restoreGeometry(element_geometries[el_name])

            #Restore state of elements
            if s_name in spyrelets_elements:
                spyreletw.load_elements_state(spyrelets_elements[s_name])
        return

    def finalize_instruments(self):
        for instrument in self.iw.instruments:
            instrument.instance.finalize()
        self.iw.instr_thread.quit()
        return

    def quit_task_threads(self):
        dockwidgets = self.spyrelet_tabs.findChildren(QtWidgets.QDockWidget)
        for spyreletw_dockwidget in dockwidgets:
            spyreletw = spyreletw_dockwidget.widget()
            spyrelet = spyreletw.spyrelet
            for task_name in spyrelet.task_names:
                task = getattr(spyrelet, task_name)
                task.task_thread.quit()
        return

    def closeEvent(self, e):
        self.save_spyrelet_geometries()
        self.finalize_instruments()
        self.quit_task_threads()
        e.accept()
        return

class SpyreApp(QtWidgets.QApplication):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_theme()
        return

    def set_theme(self):
        fusion = QtWidgets.QStyleFactory.create('Fusion')
        self.setStyle(fusion)
        dark = QtGui.QColor(53, 53, 53)
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, dark)
        palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25,25,25))
        palette.setColor(QtGui.QPalette.AlternateBase, dark)
        palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.Button, dark)
        palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
        palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
        palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
        palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
        self.setPalette(palette)
        self.setStyleSheet("QToolTip { color: #ffffff; background-color: #353535; border: 1px solid white; }")
        return
