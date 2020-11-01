##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0xF4EC::0xEE38::SDG2XCAX2R1612::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'twopulse':[
        'spyre.spyrelets.twopulse_spyrelet.TwoPulse',
        {'fungen': 'fungen'}, 
        {}
    ],
}