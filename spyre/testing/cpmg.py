##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'osc':[
        'lantz.drivers.tektronix.TDS5104',
        ['GPIB1::15::INSTR'],
        {}
    ],
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'cpmg':[
        'spyre.spyrelets.cpmg.CPMG',
        {'fungen': 'fungen','osc': 'osc'}, 
        {}
    ],
}