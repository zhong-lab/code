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
        'IV_Curve':['spyre.spyrelets.IVCurve_spyrelet.IV_Curve',
        {'srs': 'srs'},
        {}
    ],
}