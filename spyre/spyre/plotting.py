import itertools as it

from PyQt5 import QtWidgets, QtCore

import pyqtgraph as pg
from pyqtgraph.graphicsItems.GraphicsObject import GraphicsObject
from pyqtgraph import functions as fn

pg.setConfigOptions(imageAxisOrder='row-major')
import numpy as np

from .colormap import viridis
from .colors import cyclic_colors, colors
from .widgets.splitter_widget import Splitter, SplitterOrientation

from spyre.repository import pd, Node
from spyre.widgets.spinbox import SpinBox

class BasePlotWidget(QtWidgets.QWidget):

    def __init__(self, w=None, plot_item=None, parent=None):
        super().__init__(parent=parent)
        if w is None:
            w = pg.PlotWidget()
        if plot_item is None:
            plot_item = w.getPlotItem()
        self.w = w
        self.plot_item = plot_item
        self.xonbottom = True
        self.yonleft = True
        self.traces = dict()

        self._title = ''
        self._xlabel = ''
        self._ylabel = ''
        self.invertY = False
        self.invertX = False

        self.init_plot()

        return

    def init_plot(self):
        self.build_toolbox()

        splitter_config = {
            'main_w': self.w,
            'side_w': self.toolbox,
            'orientation': SplitterOrientation.vertical_left_button,
        }
        splitter = Splitter(**splitter_config)

        def show_event(ev):
            h = splitter.size().height()
            splitter.setSizes([1, 0])
            splitter.resize(h, h)

        # Collaspe the tools to start
        splitter.showEvent = show_event

        layout = QtWidgets.QGridLayout()
        layout.addWidget(splitter)
        layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(layout)
        return

    def build_toolbox(self):
        # create default tools
        self.crosshairs = CrosshairAddon(self.plot_item)

        # create toolbox and add tools
        self.toolbox = QtWidgets.QToolBox()
        self.toolbox.addItem(self.crosshairs, "Crosshairs")
        return

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, _title):
        self._title = _title
        self.plot_item.setTitle(title=_title)
        return

    @property
    def xlabel(self):
        return self._xlabel

    @xlabel.setter
    def xlabel(self, _xlabel):
        self._xlabel = _xlabel
        pos = 'bottom' if self.xonbottom else 'top'
        self.plot_item.setLabel(pos, _xlabel)
        return

    @property
    def ylabel(self):
        return self._ylabel

    @ylabel.setter
    def ylabel(self, _ylabel):
        self._ylabel = _ylabel
        pos = 'left' if self.yonleft else 'right'
        self.plot_item.setLabel(pos, _ylabel)
        return

    @property
    def invertY(self):
        return self._invertY

    @invertY.setter
    def invertY(self, invert):
        self.plot_item.getViewBox().invertY(invert)
        self._invertY = invert
        return

    @property
    def invertX(self):
        return self._invertX

    @invertX.setter
    def invertX(self, invert):
        self.plot_item.getViewBox().invertX(invert)
        self._invertX = invert
        return

    def generate_node(self, name):
        # This must be implemented for each subclass
        return None

    def load_node(self, node):
        # This must be implemented for each subclass
        pass

    def generate_meta(self, **kwargs):
        d = {'xlabel':self._xlabel, 'ylabel':self._ylabel, 'title':self._title, 'invertX':self._invertX, 'invertY':self._invertY}
        d.update(kwargs)
        return d


    def load_meta(self, meta, params=['xlabel', 'ylabel', 'title', 'invertX', 'invertY']):
        for key in params:
            if key in meta and hasattr(self, key):
                setattr(self, key, meta[key])

class HeatmapPlotWidget(BasePlotWidget):

    def __init__(self, parent=None, cmap=None):
        plot_item = pg.PlotItem(enableMouse=False)
        w = pg.ImageView(view=plot_item)
        super().__init__(parent=parent, w=w, plot_item=plot_item)
        w.ui.roiBtn.clicked.connect(self._set_roi_pos)
        self.grid(False)
        gradient = self.w.ui.histogram.gradient
        if cmap is None:
            cmap = viridis
        gradient.setColorMap(cmap)
        for tick in gradient.ticks:
            tick.hide()
        gradient.setFixedWidth(300)
        # disable gradient editing
        gradient.mouseClickEvent = lambda ev: None
        self.add_plotting_options()
        self._pos = None
        self._scale = None

        self.invertY = True
        return

    def _set_roi_pos(self):
        #Tries to place the ROI in a good spot when clicking the button
        r = np.array(self.plot_item.getViewBox().viewRange())
        pos = r.mean(axis=1)
        size = np.diff(r, axis=1)[:,0]
        if any(abs(pos-self.w.roi.pos())>abs(size)):
            self.w.roi.setPos(pos)
        if any(2*size<self.w.roi.size()):
            self.w.roi.setSize(size/2)


    def add_plotting_options(self):
        layout = QtWidgets.QVBoxLayout()
        self.plot_opts_checkboxes = dict()
        for k,val in [('autoHistogramRange',False), ('autoLevels',True), ('autoRange',True)]:
            self.plot_opts_checkboxes[k] = w = QtWidgets.QCheckBox(k)
            w.setChecked(val)
            layout.addWidget(w)
        tool_w = QtWidgets.QWidget()
        tool_w.setLayout(layout)
        self.toolbox.addItem(tool_w, "Plotting Options")


    def grid(self, toggle, alpha=0.4):
        self.plot_item.showGrid(x=toggle, y=toggle, alpha=alpha)
        return

    @property
    def im_pos(self):
        return self._pos

    @im_pos.setter
    def im_pos(self, pos):
        self._pos = pos

    @property
    def im_scale(self):
        return self._scale

    @im_scale.setter
    def im_scale(self, scale):
        self._scale = scale

    def set(self, im):
        self.w.setImage(im, pos=self._pos, scale=self._scale,
                        autoRange=self.plot_opts_checkboxes['autoRange'].isChecked(),
                        autoLevels=self.plot_opts_checkboxes['autoLevels'].isChecked(),
                        autoHistogramRange=self.plot_opts_checkboxes['autoHistogramRange'].isChecked(),)
        return

    def get(self):
        return self.w.getImageItem().image

    plot_type_str = '2DPlotWidget_v1.0'
    def generate_node(self, name):
        meta = self.generate_meta(BasePlotWidget_type=self.plot_type_str, im_scale=self.im_scale, im_pos=self.im_pos)
        return Node(name, dataframe=pd.DataFrame(self.w.getImageItem().image), metadata=meta)

    def load_node(self, node):
        meta = node.get_meta()
        if not 'BasePlotWidget_type' in meta or meta['BasePlotWidget_type'] != self.plot_type_str:
            raise Exception('Can only load data from <{}>'.format(self.plot_type_str))
        self.load_meta(meta, params=['xlabel', 'ylabel', 'title', 'im_pos', 'im_scale', 'invertX', 'invertY'])
        self.set(node.get_data().as_matrix())


class LinePlotWidget(BasePlotWidget):

    plots_updated = QtCore.pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.legend = self.w.addLegend()
        self.grid(True)
        self._colors = it.cycle(cyclic_colors)
        self.install_fitter()
        return

    def install_fitter(self):
        self.fitter = FitterWidget(self.w)
        self.fitter.traces = self.traces
        self.toolbox.addItem(self.fitter, "Fitter")
        return

    def grid(self, toggle, alpha=0.4):
        self.w.showGrid(x=toggle, y=toggle, alpha=alpha)
        return

    def plot(self, tracename, **kwargs):
        symbol_pen = kwargs.get('symbol_pen', pg.mkPen(color=(255, 255, 255, 100)))
        symbol_brush = kwargs.get('symbol_brush', pg.mkBrush(color=(255, 255, 255, 100)))
        symbol_size = kwargs.get('symbol_size', 5)
        symbol = kwargs.get('symbol', 's')
        pen = kwargs.get('pen', pg.mkPen(color=(next(self._colors) + (200,)), width=1))
        antialias = kwargs.get('antialias', False)
        trace = self.w.plot(
            symbol=symbol,
            symbolSize=symbol_size,
            symbolPen=symbol_pen,
            symbolBrush=symbol_brush,
            pen=pen,
            antialias=antialias,
        )
        trace.curve.setClickable(True)
        trace_err = None
        self.legend.addItem(trace, tracename)
        self.traces[tracename] = trace, trace_err
        self.fitter.update_traces()
        return

    def remove_trace(self, tracename):
        for item in self.traces.pop(tracename):
            self.plot_item.removeItem(item)
        self.legend.removeItem(tracename)
        self.fitter.update_traces()

    def clear(self):
        for tracename in list(self.traces.keys()):
            self.remove_trace(tracename)
        self._colors = it.cycle(cyclic_colors)

    def set(self, tracename, **kwargs):
        trace, trace_err = self.traces[tracename]
        data = kwargs.get('data')
        xs = kwargs.get('xs')
        ys = kwargs.get('ys')
        yerrs = kwargs.get('yerrs')
        if not any(item is None for item in [data, xs, ys]):
            raise ValueError('No plot points supplied (either data or xs and ys must be given)')
        if data is not None:
            xs, ys = list(zip(*data))
        if not isinstance(xs, np.ndarray):
            xs = xs.values
        if not isinstance(ys, np.ndarray):
            ys = ys.values
        trace.setData(x=xs, y=ys)
        if yerrs is not None:
            if trace_err is None:
                error_bar_params = {
                    'x': xs,
                    'y': ys,
                    'top': 0,
                    'bottom': 0,
                    'beam': 0.0,
                    'pen': pg.mkPen(color=(255, 255, 255, 80)),
                }
                trace_err = pg.ErrorBarItem(**error_bar_params)
                trace_err.setZValue(-999)
                self.w.addItem(trace_err)
                self.traces[tracename] = trace, trace_err
            ylines = list(zip(*[(yerr / 2, yerr / 2) if not np.isnan(yerr) else (0, 0) for y, yerr in zip(ys, yerrs)]))
            if ylines:
                ybottoms, ytops = ylines
                trace_err.setData(x=xs, y=ys, top=ytops, bottom=ybottoms, beam=0.0)
        return

    def get(self, tracename):
        pditem, _ = self.traces[tracename]
        x, y = pditem.getData()
        if x is None or y is None:
            return None, None
        else:
            return x.astype(np.float), y.astype(np.float)

    plot_type_str = 'LinePlotWidget_v1.0'
    def generate_node(self, name):
        data = dict()
        max_size = 0
        #Extract all the data and figure out the maximum lenght of the array
        for tracename in self.traces:
            x,y = self.get(tracename)
            if not x is None:
                data[tracename+'_x'] = x[~np.isnan(x)]
                data[tracename+'_y'] = y[~np.isnan(y)]
                max_size = max(max_size, len(data[tracename+'_x']), len(data[tracename+'_y']))
            print(max_size)

        #Resize all the array to max_size
        for tracename in data:
            temp_data = data[tracename]
            if len(temp_data)<max_size:
                new_data = np.empty(max_size)
                new_data[:] = np.NaN
                new_data[:len(temp_data)] = temp_data
                data[tracename] = new_data

        meta = self.generate_meta(BasePlotWidget_type=self.plot_type_str)
        return Node(name, dataframe=pd.DataFrame(data), metadata=meta)

    def load_node(self, node):
        meta = node.get_meta()
        if not 'BasePlotWidget_type' in meta or meta['BasePlotWidget_type'] != self.plot_type_str:
            raise Exception('Can only load data from <{}>'.format(self.plot_type_str))
        df = node.get_data()
        cols = list(df.columns)
        self.clear()
        self.load_meta(meta)
        while len(cols)>0:
            tracename = cols[0][:-2]
            x_i, y_i = cols.index(tracename+'_x'), cols.index(tracename+'_y')
            if x_i>y_i:
                x_name, y_name = cols.pop(x_i), cols.pop(y_i)
            else:
                y_name, x_name = cols.pop(y_i), cols.pop(x_i)
            x, y = df[x_name].as_matrix(), df[y_name].as_matrix()

            #Remove NaN and resize if necessary
            x,y = x[~np.isnan(x)], y[~np.isnan(y)]
            if len(x)!=len(y):
                l = min(len(x), len(y))
                x,y = x[:l], y[:l]
            self.plot(tracename)
            self.set(tracename, xs=x, ys=y)

    def __iter__(self):
        for tracename in self.traces:
            yield tracename

    def __getitem__(self, tracename):
        return self.get(tracename)



class FastImageWidget(BasePlotWidget):

    def __init__(self, parent=None):
        graphic_view = pg.GraphicsView()
        plot_item = pg.PlotItem(enableMouse=False)
        self.img_item = pg.ImageItem()
        plot_item.addItem(self.img_item)
        graphic_view.setCentralItem(plot_item)
        super().__init__(parent=parent, w=graphic_view, plot_item=plot_item)

    def set(self, image=None, autoLevels=None, **kargs):
        self.img_item.setImage(image=image, autoLevels=autoLevels, **kargs)

    plot_type_str = '2DPlotWidget_v1.0'
    def generate_node(self, name):
        meta = self.generate_meta(BasePlotWidget_type=self.plot_type_str)
        return Node(name, dataframe=pd.DataFrame(self.img_item.image), metadata=meta)

    def load_node(self, node):
        meta = node.get_meta()
        if not 'BasePlotWidget_type' in meta or meta['BasePlotWidget_type'] != self.plot_type_str:
            raise Exception('Can only load data from <{}>'.format(self.plot_type_str))
        self.load_meta(meta)
        self.set(node.get_data().as_matrix())

##---------------------------------------------------------------
##                      Crosshairs
##---------------------------------------------------------------
class Crosshair(QtCore.QObject):
    sigPositionChanged = QtCore.pyqtSignal(object)
    sigPositionChangeFinished = QtCore.pyqtSignal(object)

    def __init__(self, plot_item, pos, **kwargs):
        super().__init__()
        self.kwargs = kwargs
        self.moving = False
        self.hovering = False

        pen = fn.mkPen((255, 255, 0, 127))
        self.vLine = pg.InfiniteLine(angle=90, pen=pen, movable=False)
        self.hLine = pg.InfiniteLine(angle=0,  pen=pen, movable=False)
        self.vLine.hoverEvent, self.hLine.hoverEvent = self.hoverEvent, self.hoverEvent
        self.vLine.mouseDragEvent, self.hLine.mouseDragEvent = self.mouseDragEvent, self.mouseDragEvent

        self.center_dot = pg.ScatterPlotItem(pos=[pos], pen=fn.mkPen((255,0,0, 127)), brush=(255,0,0), symbol='o', size=3)

        plot_item.addItem(self.vLine, ignoreBounds=True)
        plot_item.addItem(self.hLine, ignoreBounds=True)
        plot_item.addItem(self.center_dot, ignoreBounds=True)
        self.plot_item = plot_item
        self.set_pos(pos)

    def set_pos(self, pos, emit_sig=True):
        if isinstance(pos, QtCore.QPointF):
            self.pos = [pos.x(), pos.y()]
        else:
            self.pos = list(pos)
        self.vLine.setPos(self.pos[0])
        self.hLine.setPos(self.pos[1])
        self.center_dot.setData(pos=[pos])
        if emit_sig: self.sigPositionChanged.emit(self.get_pos())

    def mouseDragEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            if ev.isStart():
                self.moving = True
            ev.accept()

            if not self.moving:
                return
            self.set_pos(self.plot_item.vb.mapSceneToView(ev.scenePos()))
            if ev.isFinish():
                self.moving = False
                self.sigPositionChangeFinished.emit(self.get_pos())

    def hoverEvent(self, ev):
        if (not ev.isExit()) and ev.acceptDrags(QtCore.Qt.LeftButton):
            self.hovering = True
            for line in [self.vLine, self.hLine]: line.currentPen = fn.mkPen(255, 0,0)
        else:
            self.hovering = False
            for line in [self.vLine, self.hLine]: line.currentPen = line.pen
        for line in [self.vLine, self.hLine]:
            line.update()

    def get_pos(self):
        return self.pos

    def delete(self):
        self.hLine.deleteLater()
        self.vLine.deleteLater()
        self.center_dot.deleteLater()


class CrosshairAddon(QtWidgets.QWidget):
    sigCrosshairAdded = QtCore.pyqtSignal(object)
    sigCrosshairRemoved = QtCore.pyqtSignal(object)
    def __init__(self, plot_item, **kwargs):
        super().__init__(**kwargs)
        self.plot_item = plot_item
        self.cross_list = list()
        self._spinbox_decimals = 4

        self.build_ui()


    @property
    def spinbox_decimals(self):
        return self._spinbox_decimals

    @spinbox_decimals.setter
    def spinbox_decimals(self, val):
        if self._spinbox_decimals != val:
            for r in range(self.table.rowCount()):
                self.table.cellWidget(r,0).setDecimals(val)
                self.table.cellWidget(r,1).setDecimals(val)
            self._spinbox_decimals = val

    def build_ui(self):
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['x','y','Delete'])

        #Add control (for now just an add button)
        add_btn = QtWidgets.QPushButton('+ Add')
        def add():
            r = np.array(self.plot_item.getViewBox().viewRange())
            self.add_crosshair(r.mean(axis=1))
        add_btn.clicked.connect(lambda: add())

        #Add a decimal precision box
        decimal_input = SpinBox(value=self.spinbox_decimals, minStep=1, dec=False, int=True, bounds=(0, None), step=1)
        decimal_input.valueChanged.connect(lambda x: setattr(self, 'spinbox_decimals', decimal_input.value()))

        ctrl_layout = QtWidgets.QFormLayout()
        ctrl_layout.addRow('Add Crosshair', add_btn)
        ctrl_layout.addRow('Floating point precision', decimal_input)
        ctrl_widget = QtWidgets.QWidget()
        ctrl_widget.setLayout(ctrl_layout)


        layout = QtWidgets.QGridLayout()
        layout.addWidget(ctrl_widget)
        layout.addWidget(self.table)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def add_crosshair(self, pos, **kwargs):
        # Add the Crosshair to the list
        cross = Crosshair(self.plot_item, pos, **kwargs)
        self.cross_list.append(cross)

        # Add the table entry
        row = len(self.cross_list)-1
        self.table.insertRow(row)

        # Add the x,y widgets
        def update_pos(axis, value):
            if cross.moving:
                return
            cur = cross.get_pos()
            if axis==0:
                cross.set_pos([value, cur[1]], emit_sig=False)
            elif axis==1:
                cross.set_pos([cur[0], value], emit_sig=False)
        def lambda_gen(axis):
            return lambda obj: update_pos(axis, obj.value())

        for i in range(2):
            w = SpinBox(value = pos[i], dec=True, decimals=self.spinbox_decimals)
            self.table.setCellWidget(row, i, w)
            w.sigValueChanged.connect(lambda_gen(i))


        # Add a remove button
        btn = QtWidgets.QPushButton('X')
        btn.clicked.connect(lambda: self.remove_crosshair(cross))
        self.table.setCellWidget(row, 2, btn)

        # Link the position of the cross to the numbers in the table
        cross.sigPositionChanged.connect(lambda: self.update_table_entry(cross))
        self.sigCrosshairAdded.emit(cross)


    def _find_index(self, cross):
        for i in range(len(self.cross_list)):
            if self.cross_list[i] == cross:
                return i

    def update_table_entry(self, cross):
        row = self._find_index(cross)
        self.table.cellWidget(row, 0).setValue(cross.get_pos()[0])
        self.table.cellWidget(row, 1).setValue(cross.get_pos()[1])

    def remove_crosshair(self, cross):
        index = self._find_index(cross)
        self.table.removeRow(index)
        cross.delete()
        self.cross_list.pop(index)
        self.sigCrosshairRemoved.emit(index)


    def __getitem__(self, k):
        return self.cross_list[k].get_pos()

    def __iter__(self):
        for cross in self.cross_list:
            yield cross

    def __len__(self):
        return len(self.cross_list)

from PyQt5 import Qsci, QtGui
import traceback
import inspect
from scipy import optimize

class ExpressionEditor(Qsci.QsciScintilla):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.lexer = Qsci.QsciLexerPython()
        api = Qsci.QsciAPIs(self.lexer)
        api.prepare()
        self.setLexer(self.lexer)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(Qsci.QsciScintilla.AcsAPIs)
        self.init_ui()
        return

    def init_ui(self):
        # line highlighting
        self.setCaretLineVisible(True)
        self.setCaretLineBackgroundColor(QtGui.QColor("gainsboro"))

        # autoindentation
        self.setAutoIndent(True)
        self.setIndentationGuides(True)
        self.setIndentationsUseTabs(True)
        self.setIndentationWidth(4)

        # margins
        self.setMarginsBackgroundColor(QtGui.QColor("gainsboro"))
        self.setMarginsFont(QtGui.QFont("Consolas", 9, 87))
        self.setMarginLineNumbers(1, True)
        self.setMarginLineNumbers(2, False)

        # editor font
        self.font = QtGui.QFont()
        self.font.setFamily('Consolas')
        self.font.setPointSize(10)
        self.font.setFixedPitch(True)
        self.lexer.setFont(self.font)

        # horiz scrollbar
        self.SendScintilla(self.SCI_SETHSCROLLBAR, 1)
        return

class FitterWidget(QtWidgets.QWidget):

    def __init__(self, w, parent=None):
        super().__init__(parent=parent)
        self.w = w
        self.traces = dict()
        self.fits = dict()
        self.init_ui()
        return

    def init_ui(self):
        self.plots = QtWidgets.QComboBox()
        self.editor = ExpressionEditor()
        self.update_traces()
        self.fit = QtWidgets.QPushButton('Fit')
        self.remove = QtWidgets.QPushButton('Remove fit')
        self.remove_all = QtWidgets.QPushButton('Remove all fits')
        self.fit.clicked.connect(self.compile_and_fit)
        self.remove.clicked.connect(self.remove_fit)
        self.remove_all.clicked.connect(self.remove_all_fits)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.plots)
        layout.addWidget(self.editor)
        layout.addWidget(self.fit)
        layout.addWidget(self.remove)
        layout.addWidget(self.remove_all)
        self.setLayout(layout)
        self.debug_text()
        return

    def debug_text(self):
        text = ("import numpy as np\ndef test(xs, amplitude=1, phase=0, f=1, decay=1):\n"
        "    return amplitude * np.square(np.sin(f * xs + phase)) * np.exp(-xs / decay)")
        self.editor.setText(text)
        return

    def update_traces(self):
        self.plots.clear()
        self.plots.addItems([plot_name for plot_name in sorted(self.traces.keys())])
        return

    def update_fits(self):
        for trace_name, data in self.fits.items():
            xs = data['xs']
            ys = data['ys']
            curve = data['curve']
            if curve is None:
                curve = self.w.plot(pen=pg.mkPen(color=colors['yellow'], width=1), antialias=True)
                data['curve'] = curve
            curve.setData(x=xs, y=ys)
        return

    def remove_fit(self):
        selected_trace_name = self.plots.currentText()
        try:
            fit_data = self.fits[selected_trace_name]
            fit = fit_data['curve']
        except KeyError:
            return
        self.w.removeItem(fit)
        del self.fits[selected_trace_name]
        return

    def remove_all_fits(self):
        for name in (self.plots.itemText(idx) for idx in range(self.plots.count())):
            try:
                fit_data = self.fits[name]
                fit = fit_data['curve']
            except KeyError:
                continue
            self.w.removeItem(fit)
            del self.fits[name]
        return

    def compile_and_fit(self):
        selected_trace_name = self.plots.currentText()
        editor_text = self.editor.text()
        try:
            code = compile(editor_text, '<string>', 'exec')
        except Exception as e:
            tb = e.__traceback__
        namespace = dict()
        exec(code, namespace)
        if not code.co_names:
            # raise something...no functions found
            return
        for name in code.co_names:
            try:
                f = namespace[name]
            except KeyError:
                continue
            try:
                sig = inspect.signature(f)
            except TypeError:
                continue
        var_params = list()
        for param_name, param in sig.parameters.items():
            if param.kind == param.POSITIONAL_OR_KEYWORD:
                if param.default == param.empty:
                    continue
                var_params.append((param.name, param.default))

        trace, _ = self.traces[selected_trace_name]
        plot_xs, plot_ys = trace.xData, trace.yData
        x0 = [value for _, value in var_params]
        max_nfev = 10000
        try:
            popt, pcov = optimize.curve_fit(f, plot_xs, plot_ys, p0=x0)
        except RuntimeError:
            raise
        print(popt)
        fit_ys = f(plot_xs, *popt)
        self.fits[selected_trace_name] = {
            'xs': plot_xs,
            'ys': fit_ys,
            'curve': self.fits.get(selected_trace_name, dict()).get('curve'),
        }
        self.update_fits()
        return
