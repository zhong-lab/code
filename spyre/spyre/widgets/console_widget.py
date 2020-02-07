from qtconsole.inprocess import QtInProcessKernelManager, RichJupyterWidget
from qtconsole.manager import QtKernelManager
from IPython.core.magic import Magics, magics_class, line_magic

import atexit

from jupyter_client import find_connection_file
from PyQt5 import QtCore

class Console(RichJupyterWidget):

    def __init__(self, *args, starting_namespace=dict(), **kwargs):
        super(Console, self).__init__(*args, **kwargs)
        kernel_manager = QtInProcessKernelManager()
        # kernel_manager = QtKernelManager(connection_file=find_connection_file())
        kernel_manager.start_kernel()
        kernel = kernel_manager.kernel
        # kernel.gui = 'qt5'
        kernel_client = kernel_manager.client()
        # print(kernel_client.get_user_namespace())
        kernel_client.start_channels(shell=True)
        self.kernel_manager = kernel_manager
        self.kernel_client = kernel_client
        self.shell = kernel.shell
        # self.shell.register_magics(SpyreMagics)
        self.shell.push(starting_namespace)
        self.set_default_style(colors='linux')
        return

    def push(self, namespace):
        self.shell.push(namespace)
        return

    def _banner_default(self):
        return "Spyre Console {version}\n".format(version=0.1)

@magics_class
class SpyreMagics(Magics):

    @line_magic
    def spyre(self, line):
        parser = argparse.ArgumentParser()
        args = parser.parse_args()

def test():
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication([])
    console = Console()
    console.show()
    app.exec_()

class MyFigure():

    def __init__(self):
        self._widget = GraphicsLayoutWidget()

        for i in range(5):
            self._widget.addPlot().plot(rand(100))
            self._widget.nextRow()

        QtWidgets.QApplication.processEvents()
        return

    def _repr_png_(self):

        view = self._widget
        self.image = QImage(view.viewRect().size().toSize(),
                            QImage.Format_RGB32)
        _painter = QPainter(self.image)
        view.render(_painter)

        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.ReadWrite)
        self.image.save(buffer, 'PNG')
        buffer.close()

        return bytes(byte_array)

if __name__ == '__main__':
    test()
