
"""
Smart loading of a spyre app
"""

import time
import sys
from importlib import import_module
import traceback

from spyre.widgets.spyre_widget import SpyreApp, SpyreWidget
from spyre.widgets.spyrelet_widget import SpyreletWidget
from spyre.instrument import Instrument

from main_config import spyrelets, devices


verbose = True


def main():
    app = SpyreApp([])
    spyrew = SpyreWidget()
    spyrew.persit_subpath = 'Spyre/main'

    # Initialize the instruments
    instr = dict()
    failed_device = list()
    for dname in devices.keys():
        start = time.time()
        try:
            dclass, args, kwargs = devices[dname]
            class_name = dclass.split('.')[-1]
            mod = import_module(dclass.replace('.'+class_name, ''))
            c = getattr(mod, class_name)
            instr[dname] = Instrument(c, *args, **kwargs, alias=dname)
            spyrew.iw.add_instrument(instr[dname])
        except Exception as error:
            print("Could not load "+dname)
            traceback.print_exc()
            failed_device.append(dname)
        if verbose:
            print("Loading {} took: {}sec".format(dname, time.time()-start))

    # Initialize the spyrelets
    spyrelets_dict = dict()
    unloaded_spyrelets = list(spyrelets.keys())
    failed_spyrelets = list()
    previous_len = -1
    while len(spyrelets_dict)>previous_len:
        previous_len = len(spyrelets_dict)
        for sname in unloaded_spyrelets:
            start = time.time()
            try:
                sclass, dlist, slist = spyrelets[sname]

                # Build required spyrelets list and check that all required spyrelets have been successfully loaded
                skip = False
                _slist = dict()
                for k, salias in slist.items():
                    if salias in spyrelets_dict:
                        _slist[k] = spyrelets_dict[salias]
                    else:
                        skip = True
                        break

                if not skip:
                    # Build device list and check that all the required device have been successfully loaded
                    _dlist = dict()
                    for k, dalias in dlist.items():
                        if dalias in instr:
                            _dlist[k]=instr[dalias].instance
                        else:
                            raise Exception('Spyrelet {} could not be loaded because device {} is unavailable'.format(sname, dalias))

                    # Instanciate the class
                    class_name = sclass.split('.')[-1]
                    mod = import_module(sclass.replace('.'+class_name, ''))
                    s = getattr(mod, class_name)()


                    #Set the required params
                    s.instruments = _dlist
                    s.spyrelets = _slist


                    sw = SpyreletWidget(s)
                    spyrew.spyrelet_added_handler(sw, sname)
                    spyrelets_dict[sname] = s
                    unloaded_spyrelets.remove(sname)

            except Exception as error:
                print("Could not load "+sname)
                traceback.print_exc()
                unloaded_spyrelets.remove(sname)
                failed_spyrelets.append(sname)
            if verbose:
                print("Loading {} took: {}sec".format(sname, time.time()-start))

    # Build console context
    spyrew.console.push({'spyrelets': spyrelets_dict,
                         'instr':instr
        })

    # Print report
    print("The following device could not be loaded: ")
    print(failed_device if len(failed_device)>0 else None)
    print("The following spyrelets could not be loaded: ")
    failed_spyrelets.extend(unloaded_spyrelets)
    print(failed_spyrelets)

    spyrew.restore_spyrelet_geometries()
    spyrew.showMaximized()

    sys.__excepthook__ = sys.excepthook
    sys.excepthook = spyrew.logger.handler
    app.exec_()
    return app, spyrew

if __name__ == '__main__':
    app, spyrew = main()
