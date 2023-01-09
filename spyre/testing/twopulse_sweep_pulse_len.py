##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'],
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ]
}

# Experiment List
spyrelets = {
    'twopulseecho':[
        'spyre.spyrelets.twopulse_sweep_pulse_len_spyrelet.TwoPulsePhotonEcho',
        {'fungen': 'fungen',
         'wm': 'wm'},
        {}
    ],
}