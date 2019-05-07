from PyQt5 import QtWidgets, QtGui, QtCore

import numpy as np
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.plotting import LinePlotWidget, HeatmapPlotWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_

from lantz.drivers.stanford.sg396 import SG396



default_text = """
def initialize(self):
	#INITIALIZE CODE HERE
	print('initialize...')
	return

def finalize(self):
	#FINALIZE CODE HERE
	print('finalize...')
	return

def sweep(self):
	#SWEEP CODE HERE
	self.dataset.clear()
	for i in self._sweep.progress(range(10)):
		print(i)
		values = {
					'idx': i,
				 }
		self._sweep.acquire(values)
	return

def plot1d_update(self, ev):
#    idx = self.dataset.data.idx.values
#    ev.widget.set('Signal', xs=idx, ys=idx)
	return

def plot2d_update(self, ev):
#    ev.widget.set(im)
	return
"""


class OnTheFlySpyrelet(Spyrelet):
	
	# PLaceholder for the user code
	def sweep(self):
		pass
	def initialize(self):
		pass
	def finalize(self):
		pass
	def plot1d_update(self, ev):
		pass
	def plot2d_update(self, ev):
		pass


	@Task()
	def _sweep(self, **kwargs):
		self.sweep()
		return

	@_sweep.initializer
	def _initialize(self):
		self.refresh_context()
		# exec(self.code_editor.widget.text())
		exec(self.code_editor.widget.text())
		globals().update(locals())
		glob = globals()
		def make_fun(fname): 
			return lambda *args, **kwargs: glob[fname](self, *args, **kwargs)
		for fname in ['initialize','finalize','sweep','plot1d_update','plot2d_update']:
			setattr(self, fname, make_fun(fname))
		# self.initialize = lambda *args, **kwargs: initialize(self, *args, **kwargs)
		# self.initialize = lambda *args, **kwargs: exec(test, dict(globals(), **loc), dict(initialize=loc['initialize'], self=self, args=args, kwargs=kwargs))
		# self.finalize   = lambda *args, **kwargs: loc['finalize'](self, *args, **kwargs)
		# self.sweep      = lambda *args, **kwargs: loc['sweep'](self, *args, **kwargs)
		# self.plot1d_update      = lambda *args, **kwargs: loc['plot1d_update'](self, *args, **kwargs)
		# self.plot2d_update      = lambda *args, **kwargs: loc['plot2d_update'](self, *args, **kwargs)
		self.initialize()
		return

	@_sweep.finalizer
	def _finalize(self):
		self.finalize()

	def refresh_context(self):
		for instr in self.code_editor.widget.window().iw.instruments:
			if instr.alias.isidentifier():
				self.instruments[instr.alias] = instr.instance

	@Element(name='1D PLot')
	def plot1d(self):
		p = LinePlotWidget()
		p.plot('Signal')
		return p

	@plot1d.on(_sweep.acquired)
	def _plot1d_update(self, ev):
		self.plot1d_update(ev)
		return

	@Element(name='2D PLot')
	def plot2d(self):
		p = HeatmapPlotWidget()
		return p

	@plot2d.on(_sweep.acquired)
	def _plot2d_update(self, ev):
		self.plot2d_update(ev)
		return

	@Element(name='Code Editor')
	def code_editor(self):
		editor = Scintilla_Code_Editor()
		lexer = Monokai_Python_Lexer(editor)
		editor.setLexer(lexer)
		editor.setText(default_text)
		return editor

	@Element()
	def save(self):
		w = RepositoryWidget(self)
		return w
		


class Scintilla_Code_Editor(QsciScintilla):
	def keyPressEvent(self, ev):
		if ev.modifiers() & QtCore.Qt.ControlModifier and ev.key() == QtCore.Qt.Key_Slash:
			# Commenting/Uncommenting on Ctr+/
			if self.hasSelectedText():
				isSelection = True
				selection = list(self.getSelection())
				start, _, end, _ = selection
				end += 1
			else:
				isSelection = False
				cursor_pos = list(self.getCursorPosition())
				start, _ = cursor_pos
				end = start + 1
			self.setSelection(start,0,end,0)
			text = self.selectedText()
			split = text.split('\n')
			if all([line=='' or line[0]=='#' for line in split]): #Need to uncomment if line starts with '#'
				new_split = ['' if line=='' else line[1:] for line in split]
			else: #Need to comment
				new_split = ['' if line=='' else '#'+line for line in split]
			new_text = '\n'.join(new_split)
			self.removeSelectedText()
			self.insert(new_text)

			if isSelection:
				selection[3] += len(new_text)-len(text)
				self.setSelection(*selection)
			else:
				cursor_pos[1] += len(new_text)-len(text)
				self.setCursorPosition(*cursor_pos)
			ev.accept()
		else:
			super().keyPressEvent(ev)

class Monokai_Python_Lexer(QsciLexerPython):
	def __init__(self, editor, *args):
		super().__init__(editor, *args)

		#Margins
		editor.setMarginLineNumbers(1, True)
		editor.setMarginWidth(1, '99999')
		editor.setMarginsBackgroundColor(QtGui.QColor("#272822"))
		editor.setMarginsForegroundColor(QtGui.QColor('#75715e'))

		#Cursor
		editor.ensureCursorVisible()
		editor.setCaretForegroundColor(QtGui.QColor('white'))
		editor.setCaretWidth(2)

		#Indentation
		editor.setAutoIndent(True)
		editor.setIndentationsUseTabs(False)
		editor.setTabWidth(4)


		self.setDefaultPaper(QtGui.QColor("#272822"))
		font = QtGui.QFont('Courier New',12)
		self.setFont(font)

		self.setIndentationWarning(QsciLexerPython.Inconsistent)
		self.setHighlightSubidentifiers(False)

		self.setColor(QtGui.QColor('#9081ff'), QsciLexerPython.Number) ## Purple
		self.setColor(QtGui.QColor('#66d9ef'), QsciLexerPython.HighlightedIdentifier )## Blue
		self.setColor(QtGui.QColor('#e2266d'), QsciLexerPython.Keyword) ## keyword red
		self.setColor(QtGui.QColor('white'), QsciLexerPython.Operator) ## White
		self.setColor(QtGui.QColor('#75715e'), QsciLexerPython.Comment) ## Comment Gray

		self.setColor(QtGui.QColor('#e6db5a'), QsciLexerPython.DoubleQuotedString) ## String Yellow
		self.setColor(QtGui.QColor('#e6db5a'), QsciLexerPython.SingleQuotedString) ## String Yellow
		self.setColor(QtGui.QColor('#e6db5a'), QsciLexerPython.TripleSingleQuotedString) ## String Yellow
		self.setColor(QtGui.QColor('#e6db5a'), QsciLexerPython.TripleDoubleQuotedString) ## String Yellow
		
		self.setColor(QtGui.QColor('#a6e22e'), QsciLexerPython.ClassName) ## Green
		self.setColor(QtGui.QColor('#a6e22e'), QsciLexerPython.FunctionMethodName) ## Green
		self.setColor(QtGui.QColor('#a6e22e'), QsciLexerPython.Decorator) ## Green

	def keywords(self, s):
		# if s == 1:
		#     return super().keywords(s) + '+ - * / =='
		if s == 2:
			special_func = '__abs__ __add__ __and__ __call__ __class__ __cmp__ __coerce__ __complex__ __contains__ __del__ __delattr__ __delete__ __delitem__ __delslice__ __dict__ __div__ __divmod__ __eq__ __float__ __floordiv__ __ge__ __get__ __getattr__ __getattribute__ __getitem__ __getslice__ __gt__ __hash__ __hex__ __iadd__ __iand__ __idiv__ __ifloordiv__ __ilshift__ __imod__ __imul__ __index__ __init__ __instancecheck__ __int__ __invert__ __ior__ __ipow__ __irshift__ __isub__ __iter__ __itruediv__ __ixor__ __le__ __len__ __long__ __lshift__ __lt__ __metaclass__ __mod__ __mro__ __mul__ __ne__ __neg__ __new__ __nonzero__ __oct__ __or__ __pos__ __pow__ __radd__ __rand__ __rcmp__ __rdiv__ __rdivmod__ __repr__ __reversed__ __rfloordiv__ __rlshift__ __rmod__ __rmul__ __ror__ __rpow__ __rrshift__ __rshift__ __rsub__ __rtruediv__ __rxor__ __set__ __setattr__ __setitem__ __setslice__ __slots__ __str__ __sub__ __subclasscheck__ __truediv__ __unicode__ __weakref__ __xor__'
			built_in = 'abs divmod input open staticmethod all enumerate int ord str any eval isinstance pow sum basestring execfile issubclass print super bin file iter property tuple bool filter len range type bytearray float list raw_input unichr callable format locals reduce unicode chr frozenset long reload vars classmethod getattr map repr xrange cmp globals max reversed zip compile hasattr memoryview round __import__ complex hash min set  delattr help next setattr  dict hex object slice  dir id oct sorted'
			return "class def lambda None True False " + special_func + built_in 
		else:
			return super().keywords(s)

	# def add_comment_block(self):
	#     editor = self.editor()
	#     def 
