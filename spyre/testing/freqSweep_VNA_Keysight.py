##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'vna':[
        'lantz.drivers.VNA_Keysight.E5071B',
        ['TCPIP0::A-E5071B-03400::inst0::INSTR'],
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
    'freqSweep_Keysight':[
        'spyre.spyrelets.freqSweep_VNA_Keysight_spyrelet.Sweep',
        {'vna': 'vna','source': 'source'}, 
        {}
    ],

}