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
    'srs':[
        'lantz.drivers.stanford.srs900.SRS900',
        ['GPIB0::2::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'lifetimewithshutter':[
        'spyre.spyrelets.lifetimewithshutter_spyrelet.Lifetimewithshutter',
        {'fungen': 'fungen', 'wm':'wm', 'srs':'srs'}, 
        {}
    ],
}