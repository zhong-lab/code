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
}

# Experiment List
spyrelets = {
    'Er2O3_spectroscopy':[
        'spyre.spyrelets.Er2O3_Noah_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
        },
        {}
    ],
}
