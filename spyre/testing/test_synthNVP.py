# Device List
devices = {
    'windfreak':[
        'lantz.drivers.windfreak.synthnvpro.SynthNVPro',
        ['ASRL7::INSTR'], # connecting windfreak, the port number could change time to time
        {}
    ]
}

# Experiment List
spyrelets = {
    'test_SynthNVP': [
        'spyre.spyrelets.test_synthNVP_spyrelet.TestSynthNVP',
        {'windfreak': 'windfreak'},
        {}
    ],
}