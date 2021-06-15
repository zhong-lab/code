devices = {
    'osa':[
        'lantz.drivers.ando.aq6317b.AQ6317B',
        ['GPIB0::1::INSTR'],   # optical spectrum analyzer
        {}
    ],
    'tc':[
        'lantz.drivers.artisan.ldt5910b.LDT5910B',
        ['GPIB1::2::INSTR'],   # temperature controller
        {}
    ]
}

# Experiment List
spyrelets = {
    'filter':[
        'spyre.spyrelets.peaktrack_spyrelet.filter',
        {
            'osa':'osa',
            'tc':'tc',
        },
        {}
    ],
}
