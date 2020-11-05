devices = {
    # 'delaygen':[
    #     'lantz.drivers.stanford.DG645',
    #     ['TCPIP0::169.254.29.167::inst0::INSTR'], # connect delay generator by ethernet and use for triggering shutter
    #     {}
    # ],
    'fungen':[
        'lantz.drivers.keysight.SDG2122X.SDG2122X',
        ['USB0::0xF4EC::0xEE38::SDG2XCAX2R1612::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
    # 'wm':[
    #     'lantz.drivers.bristol.bristol771.Bristol_771',
    #     [6535],
    #     {}
    # ]
}

# Experiment List
spyrelets = {
    'voltage_scan':[
        'spyre.spyrelets.voltage_scan_spyrelet.fiberfilter_scan',
        {   
            # 'delaygen':'delaygen'
            'fungen': 'fungen',
            # 'wm':'wm'
        }, 
        {}
    ],

}