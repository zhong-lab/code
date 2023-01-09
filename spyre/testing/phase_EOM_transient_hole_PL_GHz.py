devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
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
    'PLCounts':[
        'spyre.spyrelets.phase_EOM_transient_hole_PL_GHz_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm': 'wm',
            'analyzer': 'analyzer'
        },
        {}
    ],
}

