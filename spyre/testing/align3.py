# Device List
devices = {
    'powermeter':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ]
}


# Experiment List
spyrelets = {
    'align':[
        'spyre.spyrelets.align3_spyrelet.ALIGNMENT',
        {'powermeter': 'powermeter'},
        {}
    ],

  
}