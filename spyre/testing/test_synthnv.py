# Device List
devices = {
    # 'windfreak':[
    #     'lantz.drivers.windfreak.synthnv.SynthNV',
    #     ['ASRL11::INSTR'], # connecting windfreak, the port number could change time to time
    #     {}
    # ]
    'wm': [
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ]
}

# Experiment List
spyrelets = {
    'test_SynthNV': [
        'spyre.spyrelets.test_synthnv_spyrelet.TestSynthNV',
        {
            'wm': 'wm'
        },
        {}
    ],
}