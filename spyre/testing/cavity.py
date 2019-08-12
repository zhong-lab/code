##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'vna':[
        'lantz.drivers.VNA.P9371A',
        ['TCPIP0::DESKTOP-ER250Q8::hislip0,4880::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'freqSweep':[
        'spyre.spyrelets.cavity_spyrelet.Record',
        {'vna': 'vna'}, 
        {}
    ],

}