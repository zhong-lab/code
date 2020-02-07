# Device List
devices = {
    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0022812::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'biconicalpull':[
        'spyre.spyrelets.biconicalpull_spyrelet.FiberPulling',
        {'pmd': 'pmd'},
        {}
    ],
}
