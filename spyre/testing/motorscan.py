enable_restore_geometry=True

devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ],
    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
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
    'heterodyneecho':[
        'spyre.spyrelets.motorscan_spyrelet2.MotorScan',
        {'fungen': 'fungen','pmd': 'pmd','wm':'wm'}, 
        {}
    ],

}