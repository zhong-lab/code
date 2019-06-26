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
    'photoncounts':[
        'spyre.spyrelets.photoncounts_spyrelet.PhotonCount',
        {'srs': 'srs'},
        {}
    ],
}