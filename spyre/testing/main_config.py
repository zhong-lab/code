# Device List
devices = {
    # 'spa':[
    #     'lantz.drivers.anritsu.MS2721B',
    #     ['USB0::0x0B5B::0xFFF9::1001042_146_11::INSTR'],
    #     {}
    # ],
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ],
    'osc':[
        'lantz.drivers.tektronix.tds2024c.TDS2024C',
        ['USB0::0x0699::0x03A6::C030873::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    # 'spectrum':[
    #     'spyre.spyrelets.SpectrumAnalyzer',
    #     {'spa': 'spa'}, 
    #     {'spectrum': 'spectrum'}
    # ],
    'laser calibration':[
        'spyre.spyrelets.onthefly.OnTheFlySpyrelet',
        {'fungen': 'fungen'}, 
        {}
    ],
}