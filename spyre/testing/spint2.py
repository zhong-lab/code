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
    ], 
    'delaygen':[
        'lantz.drivers.stanford.DG645',
        ['TCPIP0::169.254.29.167::inst0::INSTR'],
        {}
    ],
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'spin_echo1':[
        'spyre.spyrelets.Spin_T2.Record',
        {'osc': 'osc','source':'source','delaygen': 'delaygen','fungen':'fungen'},
        {}
    ],

}