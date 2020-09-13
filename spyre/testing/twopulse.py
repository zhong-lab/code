# Device List
devices = {
    'delaygen':[
        'lantz.drivers.stanford.DG645',
        ['TCPIP0::169.254.29.167::inst0::INSTR'],
        {}
    ],
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'spin_echo':[
        'spyre.spyrelets.TwoPulse.Record',
        {'delaygen': 'delaygen','fungen':'fungen'},
        {}
    ],

}