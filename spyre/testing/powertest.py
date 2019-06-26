# Device List
devices = {
    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'powertest':[
        'spyre.spyrelets.powermetertest_spyrelet.Test',
        {'pmd': 'pmd'},
        {}
    ],
}