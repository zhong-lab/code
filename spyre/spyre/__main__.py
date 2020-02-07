def main():
    import sys, os
    if sys.executable.endswith("pythonw.exe"):
        # sys.stdout = open(os.devnull, "w")
        sys.stdout = open(os.path.join(os.getenv("APPDATA"), 'Spyre', "stdout.txt"), 'w')
        sys.stderr = open(os.path.join(os.getenv("APPDATA"), 'Spyre', "stderr.txt"), "w")
    from spyre.instrument import InstrumentMediator, InstrumentPresenter
    from spyre.widgets.instrument_widget import InstrumentWidget
    from spyre.widgets.console_widget import Console
    from spyre.spyre import Spyre
    from spyre.widgets.spyre_widget import SpyreApp, SpyreWidget, SpyrePresenter

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
    }
    console.push(starting_namespace)

    sw.showMaximized()
    app.exec_()
    return
