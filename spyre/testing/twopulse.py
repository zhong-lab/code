##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
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
    'twopulse':[
        'spyre.spyrelets.twopulse_spyrelet.TwoPulse',
        {'fungen': 'fungen', 'srs':'srs'}, 
        {}
    ],
}