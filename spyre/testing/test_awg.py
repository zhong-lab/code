devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ]
}

# Experiment List
spyrelets = {
    'Test':[
        'spyre.spyrelets.test_awg_spyrelet.Test',
        {
            'fungen': 'fungen',
        },
        {}
    ],
}
