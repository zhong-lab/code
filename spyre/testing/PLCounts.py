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
    'windfreak': [
        'lantz.drivers.windfreak.synthnvpro.SynthNVPro',
        ['ASRL7::INSTR'],  # connecting windfreak, the port number could change time to time
        {}
    ]
}

# Experiment List
spyrelets = {
    'PLCounts':[
        'spyre.spyrelets.PLCounts_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
            'windfreak': 'windfreak'
        },
        {}
    ],
}
