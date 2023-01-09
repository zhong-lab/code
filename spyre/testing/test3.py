# Device List
devices = {
'analyzer': [
        'lantz.drivers.spectrum.MS2721B',
        ['USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'test': [
        'spyre.spyrelets.test3_spyrelet.Test',
        {'analyzer': 'analyzer'},
        {}
    ],
}
