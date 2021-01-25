# Device List
devices = {
    'osc':[
        'lantz.drivers.tektronix.TDS5104',
        ['GPIB1::15::INSTR'],
        {}
    ],
    'source':[
        'lantz.drivers.keysight.N5181A',
        ['TCPIP0::A-N5181A-41097::inst0::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'spin_echo1':[
        'spyre.spyrelets.HDAWG.SpinT2.Record',
        {'osc': 'osc','source':'source'},
        {}
    ],

}