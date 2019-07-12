# Device List
devices = {
    'gpd':[
        'lantz.drivers.gwinstek.g3303s.GPD3303S',
        ['ASRL22::INSTR'],
        {}
    ],
    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'testpull':[
        'spyre.spyrelets.testpull_spyrelet.FiberPulling',
        {'gpd': 'gpd', 'pmd': 'pmd'},
        {}
    ],
}