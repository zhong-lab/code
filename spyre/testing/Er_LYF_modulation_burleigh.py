# Device List
devices = {
    'wm': [
        'lantz.drivers.burleigh.WA7600',
        ['GPIB1::10::INSTR'],
        {}
    ],
    'analyzer': [
        'lantz.drivers.spectrum.MS2721B',
        ['USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'modulation': [
        'spyre.spyrelets.Er_LYF_modulation_burleigh_spyrelet.SweepSignal',
        {'wm': 'wm', 'analyzer': 'analyzer'},
        {}
    ],
}
