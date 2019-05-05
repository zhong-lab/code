##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],
    'qutag':[
        'lantz.drivers.qutools.qutag2.QuTAG2',
        [],
        {}
    ]
}

# Experiment List
spyrelets = {
    'lifetime':[
        'spyre.spyrelets.lifetime_spyrelet.Lifetime',
        {'fungen': 'fungen',
        'wm':'wm','qutag':'qutag'}, 
        {}
    ],
}