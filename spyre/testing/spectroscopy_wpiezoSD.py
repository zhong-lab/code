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
    'source':[
        'lantz.drivers.agilent.N5181A',
        ['TCPIP0::A-N5181A-41097::inst0::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'PLpiezo_cwicker':[
        'spyre.spyrelets.spectroscopy_wpiezoSD_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
            'source':'source'
        }, 
        {}
    ],
}