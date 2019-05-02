import os

from PyQt5 import QtWidgets, QtCore, QtGui

class ControlWidget(QtWidgets.QWidget):

    run_state = QtCore.pyqtSignal(str, int, bool)

    def __init__(self, axes):
        super().__init__()
        self.axes = axes
        self.init_ui()

    def init_ui(self):
        layout = QtWidgets.QGridLayout()
        row, column = 1, 1
        for axis_name, axis_opts in self.axes:
            orientation = axis_opts.get('orientation')
            if orientation == 'vertical':
                self.button_one = ArrowButton('up')
                self.button_two = ArrowButton('down')
                layout.addWidget(self.button_one, row-1, column, QtCore.Qt.AlignBottom)
                layout.addWidget(self.button_two, row+1, column, QtCore.Qt.AlignTop)
                column = column + 2
            else:
                self.button_one = ArrowButton('left')
                self.button_two = ArrowButton('right')
                layout.addWidget(self.button_one, row, 0, QtCore.Qt.AlignRight)
                layout.addWidget(self.button_two, row, 2, QtCore.Qt.AlignLeft)
                row = row + 2
            limits = axis_opts.get('limits')
            self.button_one.setFixedSize(50,50)
            self.button_two.setFixedSize(50,50)
            self.exec_(axis_name, limits)
        self.setLayout(layout)
        return

    def exec_(self, axis_name, limits):
        self.button_one.pressed.connect(lambda: self.run_state.emit(axis_name, limits[1], True))
        self.button_two.pressed.connect(lambda: self.run_state.emit(axis_name, limits[0], True))
        self.button_one.released.connect(lambda: self.run_state.emit(axis_name, limits[1], False))
        self.button_two.released.connect(lambda: self.run_state.emit(axis_name, limits[0], False))

class ArrowButton(QtWidgets.QToolButton):
    def __init__(self, orientation):
        super().__init__()
        self.orientation = orientation
        self.init_ui()

    def init_ui(self):
        image_path = os.path.join(os.path.dirname(__file__),'..\\images\\')
        image_path = image_path.replace("\\","/")
        pressed = image_path + '{}_arrow_pressed.png'
        unpressed = image_path + '{}_arrow_unpressed.png'
        orientation = self.orientation
        button_style = '''
            background-image: url({image});
            background-repeat: no-repeat;
            background-position: center;
            background-color: {background};
            border-{corner1}-radius: 10px;
            border-{corner2}-radius: 10px;
            border-color: rgb(33,33,33);
            border-style: outset;
            border-width: 1.5px;
        '''
        params_pressed = {
            'image': pressed.format(orientation),
            'background': 'rgb(53,53,53)',
            'corner1': 'bottom-{}'.format(orientation),
            'corner2': 'top-{}'.format(orientation),
        }
        params_unpressed = {
            'image': unpressed.format(orientation),
            'background': 'rgb(61,61,61)',
            'corner1': 'bottom-{}'.format(orientation),
            'corner2': 'top-{}'.format(orientation),
        }

        if orientation == 'up':
            params_unpressed['corner1'] = 'top-right'
            params_unpressed['corner2'] = 'top-left'
            params_pressed['corner1'] = params_unpressed['corner1']
            params_pressed['corner2'] = params_unpressed['corner2']

        elif orientation == 'down':
            params_unpressed['corner1'] = 'bottom-right'
            params_unpressed['corner2'] = 'bottom-left'
            params_pressed['corner1'] = params_unpressed['corner1']
            params_pressed['corner2'] = params_unpressed['corner2']

        self.button_style_pressed = button_style.format(**params_pressed)
        self.button_style_unpressed = button_style.format(**params_unpressed)
        self.setStyleSheet(self.button_style_unpressed)

    def mousePressEvent(self, ev):
        self.setStyleSheet(self.button_style_pressed)
        QtWidgets.QToolButton.mousePressEvent(self, ev)

    def mouseReleaseEvent(self, ev):
        self.setStyleSheet(self.button_style_unpressed)
        QtWidgets.QToolButton.mouseReleaseEvent(self, ev)

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication([])
    axes = [
    ('y axis', {
        'orientation': 'vertical',
        }),
    ('x axis', {
        'orientation': 'horizontal',
        }),
    ]
    c = ControlWidget(axes)
    c.show()
    app.exec_()
