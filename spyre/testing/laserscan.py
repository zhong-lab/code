# Device List
devices = {
    'wm':[
        'lantz.drivers.bristol',
        ['TCPIP0::DESKTOP-ER250Q8::hislip0,4880::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan_spyrelet.LaserScan',
        {'wm': 'wm'}, 
        {}
    ],

}