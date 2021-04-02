devices = {

    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],

    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0022812::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan_wm_spyrelet.LaserScan',
        {
            'pmd':'pmd', 
            'wm':'wm'
        },
        {}
    ],

}