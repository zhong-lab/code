# Device List
devices = {
    'wm': [
        'lantz.drivers.burleigh.WA7600',
        ['GPIB1::10::INSTR'],
        {}
    ],
}

# Experiment List
spyrelets = {
    'test1': [
        'spyre.spyrelets.test_burleigh_spyrelet.TestBurleigh',
        {
        'wm': 'wm'},
        {}
    ],
}
