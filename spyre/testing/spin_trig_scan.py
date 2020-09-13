
# Device List
devices = {
    'osc':[
        'lantz.drivers.tektronix.TDS5104',
        ['GPIB1::15::INSTR'],
        {}
    ],
    'source':[
        'lantz.drivers.mwsource.SynthNVPro',
        ['ASRL8::INSTR'],
        {}
    ],
    'delaygen':[
        'lantz.drivers.stanford.DG645',
        ['TCPIP0::169.254.29.167::inst0::INSTR'],
        {}
    ]

}
# Experiment List
spyrelets = {
    'spin_trig_scan':[
        'spyre.spyrelets.spin_trig_scan.Record',
        {'osc': 'osc','source':'source','delaygen': 'delaygen'},
        {}
    ],

}