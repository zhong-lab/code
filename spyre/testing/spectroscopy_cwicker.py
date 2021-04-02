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
    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ]
    #'SRS':[
    #    'lantz.drivers.stanford.srs900.SRS900',
    #    ['GPIB0::2::INSTR'],   ##SRS - power suppy for the SNSPD
    #    {}
    #]
}

# Experiment List
spyrelets = {
    'spectroscopy_cwicker':[
        'spyre.spyrelets.spectroscopy_cwicker_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
            'pmd':'pmd'
            #'SRS':'SRS',
        }, 
        {}
    ],
}