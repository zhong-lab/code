# Device List
devices = {
    'srs':[
        'lantz.drivers.stanford.srs900.SRS900',
        ['GPIB0::2::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'IVcurve':[
        'spyre.spyrelets.darkcount_spyrelet.IVcurve',
        {'srs': 'srs'},
        {}
    ],
}