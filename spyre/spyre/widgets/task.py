from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import SignalProxy

class TaskWidget(QtWidgets.QWidget):

    def __init__(self, task, rate_limit=0.01, parent=None):
        super().__init__(parent=parent)
        self.task = task
        self.init_ui()
        proxy_config = {
            'signal': self.task.progressed,
            'delay': 0.01,
            'rateLimit': rate_limit,
            'slot': self.update,
        }
        self.task.exception_raised.connect(lambda: self.update_run_state(state='error'))
        self.task.running.connect(lambda r: self.update_run_state(state='run' if r else 'stop'))
        self.proxy = SignalProxy(**proxy_config)
        self.running = False

        return

    def init_ui(self):
        task_label = QtWidgets.QLabel('<h3>{}</h3>'.format(self.task.name))

        control_layout = QtWidgets.QHBoxLayout()
        play_icon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay)
        stop_icon = self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop)
        start_button = QtWidgets.QToolButton()
        stop_button = QtWidgets.QToolButton()

        start_button.clicked.connect(lambda: self.run_state(state='run'))
        stop_button.clicked.connect(lambda: self.run_state(state='stop'))

        start_button.setIcon(play_icon)
        stop_button.setIcon(stop_icon)
        control_layout.addWidget(start_button)
        control_layout.addWidget(stop_button)

        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(task_label)
        top_layout.addLayout(control_layout)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)

        self.time_label = QtWidgets.QLabel()
        self.state_label = QtWidgets.QLabel()
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(self.time_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.state_label)

        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.addLayout(top_layout)
        outer_layout.addWidget(self.progress_bar)
        outer_layout.addLayout(bottom_layout)

        self.setLayout(outer_layout)
        return

    @QtCore.pyqtSlot(object)
    def update(self, args):
        if not self.running:
            return
        depth, n, total, elapsed = args
        if total is not None:
            iter_word = 'iterations' if total > 1 else 'iteration'
            pct = 100 * n / total
            if n:
                tot_time = (elapsed / n) * total
                rem_time = tot_time - elapsed
            else:
                rem_time = None
            progfmt = "{completed} of {total} {iter_word} complete ({pct:1.1f}%)"
            self.progress_bar.setFormat(progfmt.format(**{
                'completed': n,
                'total': total,
                'iter_word': iter_word,
                'pct': pct,
            }))
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(pct)
            timefmt = "{elapsed:s} elapsed" if rem_time is None else "{elapsed:s} elapsed; {rem:s} remaining"
            self.time_label.setText(timefmt.format(**{
                'elapsed': readable_seconds(elapsed),
                'rem': readable_seconds(rem_time) if rem_time is not None else None,
            }))
        else:
            iter_word = 'iterations' if n > 1 else 'iteration'
            progfmt = "{completed} {iter_word} complete"
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(progfmt.format(**{
                'completed': n,
                'iter_word': iter_word,
            }))
            timefmt = "{elapsed:s} elapsed"
            self.time_label.setText(timefmt.format(**{
                'elapsed': readable_seconds(elapsed),
            }))
        return

    def run_state(self, state):
        if state == 'run':
            self.task()
            self.running = True
        if state == 'error':
            pass
        if state == 'stop':
            self.task.stop()
            self.running = False
        self.update_run_state(state)
        return

    def update_run_state(self, state):
        if state == 'run':
            self.state_label.setText('Running')
        if state == 'error':
            self.state_label.setText('Exception encountered')
        if state == 'stop':
            self.state_label.setText('Stopped')
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        return

def readable_seconds(seconds):
    seconds = int(seconds)
    if not seconds:
        return '0 s'
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    htext = '{} h'.format(hours) if hours else ''
    mtext = '{} m'.format(mins) if mins else ''
    stext = '{} s'.format(secs) if secs else ''
    readable = ' '.join(v for v in (htext, mtext, stext) if v)
    return readable
