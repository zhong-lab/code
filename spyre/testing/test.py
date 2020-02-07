from test_driver import TestDriver

def test():
    import sys, os
    if sys.executable.endswith("pythonw.exe"):
        sys.stdout = open(os.devnull, "w");
        sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")
    from spyre.instrument import InstrumentMediator, InstrumentPresenter
    from spyre.widgets.instrument_widget import InstrumentWidget
    from spyre.widgets.console_widget import Console
    from spyre.spyre import Spyre
    from spyre.widgets.spyre_widget import SpyreApp, SpyreWidget, SpyrePresenter
    from spyre.spyrelets.lockinvsfreq import LockinVsFreq
    from spyre.spyrelets.taskvstime import TaskVsTime

    app = SpyreApp([])

    im = InstrumentMediator()
    iw = InstrumentWidget()
    ip = InstrumentPresenter(im, iw)

    spyre = Spyre(im)


    console = Console()

    sw = SpyreWidget(iw, console)
    presenter = SpyrePresenter(spyre, sw)
    starting_namespace = {
        'spyre': spyre,
        'sp': presenter,
    }
    console.push(starting_namespace)

    sw.showMaximized()
    # spyre.add_spyrelet(LockinVsFreq)
    # spyre.add_spyrelet(TaskVsTime)
    app.exec_()
    return

if __name__ == '__main__':
    test()
