# Device List
devices = {
    'SRS':[
        'lantz.drivers.stanford.srs900.SRS900',
        ['GPIB0::2::INSTR'],   ##SRS - power suppy for the SNSPD
        {}
    ]
}

# Experiment List
spyrelets = {
    'test_SRS': [
        'spyre.spyrelets.test_SRS_spyrelet.TestSRS',
        {'SRS':'SRS'},
        {}
    ],
}
