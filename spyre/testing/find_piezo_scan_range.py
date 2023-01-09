# Device List
devices = {
    'wm': [
        'lantz.drivers.burleigh.WA7600',
        ['GPIB1::10::INSTR'],
        {}
    ],
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ]
}

# Experiment List
spyrelets = {
    'find_piezo_scan_range': [
        'spyre.spyrelets.find_piezo_scan_range_spyrelet.FindPiezoScanRange',
        {
        'wm': 'wm',
        'fungen': 'fungen',
        },
        {}
    ],
}
