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
    'align':[
        'spyre.spyrelets.align3_cwicker_spyrelet.ALIGNMENT',
        {'pmd':'pmd'},
        {}
    ],

}
