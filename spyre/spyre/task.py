from PyQt5 import QtCore

from functools import partial, wraps, update_wrapper
import time
import warnings

class TaskProxy(QtCore.QObject):

    start = QtCore.pyqtSignal(object, object, object)
    running = QtCore.pyqtSignal(bool)
    exception = QtCore.pyqtSignal(Exception)
    done = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.start.connect(self.exec_)
        return

    @QtCore.pyqtSlot(object, object, object)
    def exec_(self, init, final, partialed):
        self.running.emit(True)
        with warnings.catch_warnings():
            warnings.simplefilter('once')
            try:
                init()
                partialed()
            except StopIteration:
                pass
            except Exception as e:
                self.exception.emit(e)
            finally:
                try:
                    final()
                except Exception as e:
                    self.exception.emit(e)
        self.running.emit(False)
        self.done.emit()
        return

class TaskDecorator(object):

    def __init__(self, decor, instance):
        self.decor = decor
        self.instance = instance
        return

    def __call__(self, *args, **kwargs):
        return self.decor(self.instance, *args, **kwargs)

    def __getattr__(self, key):
        return getattr(self.decor, key)

    def __repr__(self):
        return '<bound method {} of {}>'.format(self.decor, type(self))

class TaskWrapper(QtCore.QObject):

    _spyre_task = True

    running = QtCore.pyqtSignal(bool)
    new_row = QtCore.pyqtSignal(object)
    acquired = QtCore.pyqtSignal(object)
    progressed = QtCore.pyqtSignal(int, int, object, float)
    exception_raised = QtCore.pyqtSignal()

    def __init__(self, task_init_f, name=None, parent=None):
        super().__init__(parent=parent)

        self.task_init_f = task_init_f
        self.initialize = lambda *args, **kwargs: None
        self.finalize = lambda *args, **kwargs: None

        self.main_thread_id = self.get_thread_id()
        self.stop_requested = False

        self.task_thread = QtCore.QThread()
        self.task_thread.start()

        self.proxies = list()
        self._progress_depth = 0

        update_wrapper(self, task_init_f)
        self.name = task_init_f.__name__ if name is None else name
        return

    def initializer(self, f):
        self.initialize = f
        return f

    def finalizer(self, f):
        self.finalize = f
        return f

    def __call__(self, spyrelet, *args, **kwargs):
        if not spyrelet.runnable:
            raise RuntimeError('spyrelet not runnable...')

        proxy = TaskProxy()
        self.proxies.append(proxy)
        proxy.moveToThread(self.task_thread)
        proxy.running.connect(self.running)
        proxy.done.connect(partial(self.pop_proxy, spyrelet))
        proxy.exception.connect(self.handle_exception)
        try:
            self.new_row.disconnect(spyrelet.acquire)
        except TypeError:
            pass
        finally:
            self.new_row.connect(spyrelet.acquire)
        try:
            self.progressed.disconnect(spyrelet.progressed)
        except TypeError:
            pass
        finally:
            self.progressed.connect(spyrelet.progressed)


        p_init = partial(self.initialize, spyrelet)
        p_final = partial(self.finalize, spyrelet)
        p_func = partial(self.task_init_f, spyrelet, *args, **kwargs)
        async = (self.get_thread_id() == self.main_thread_id)
        if async:
            proxy.start.emit(p_init, p_final, p_func)
        else:
            proxy.exec_(p_init, p_final, p_func)
        return

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return TaskDecorator(self, instance)

    def pop_proxy(self, instance):
        proxy = self.sender()
        self.proxies.remove(proxy)
        return

    def get_thread_id(self):
        return int(self.thread().currentThreadId())

    def acquire(self, value):
        self.new_row.emit(value)
        if self.stop_requested:
            self.stop_requested = False
            raise StopIteration

    def progress(self, iterable, miniters=1, mininterval=0.1, name=None):
        # adapted from tqdm core
        try:
            total = len(iterable)
        except TypeError:
            total = None

        start_t = last_print_t = time.time()
        last_print_n = 0
        n = 0
        # self._progress_depth += 1
        current_depth = self._progress_depth

        try:
            for obj in iterable:
                yield obj
                n += 1
                if n - last_print_n >= miniters:
                    curr_t = time.time()
                    if curr_t - last_print_t >= mininterval:
                        elapsed = curr_t - start_t
                        self.progressed.emit(current_depth, n, total, elapsed)
                        last_print_n = n
                        last_print_t = curr_t
        except GeneratorExit:
            pass
        finally:
            self.progressed.emit(current_depth, n, total, time.time() - start_t)
            # self._progress_depth -= 1
        return

    def handle_exception(self, exc):
        self.exception_raised.emit()
        raise exc

    def stop(self):
        self.stop_requested = True
        return


class Task(object):

    def __init__(self, name=None):
        self.name = name
        return

    def __call__(self, func):
        wrapper = TaskWrapper(func, name=self.name)
        return wrapper
