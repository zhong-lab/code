##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'vna':[
        'lantz.drivers.VNA.P9371A',
        ['TCPIP0::DESKTOP-ER250Q8::hislip0,4880::INSTR'],
        {}
    ],
    'source':[
        'lantz.drivers.mwsource.SynthNVPro',
        ['ASRL16::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'freqSweep':[
        'spyre.spyrelets.freqSweep_VNA_spyrelet.Sweep',
        {'vna': 'vna','source': 'source'}, 
        {}
    ],

}