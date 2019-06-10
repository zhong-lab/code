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
    ]
}

# Experiment List
spyrelets = {
    'bulkT1':[
        'spyre.spyrelets.bulkT1_spyrelet.BulkT1',
        {'fungen': 'fungen',
        'wm':'wm'}, 
        {}
    ],
}