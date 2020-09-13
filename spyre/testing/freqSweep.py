##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'analyzer':[
        'lantz.drivers.spectrum.MS2721B',
        ['USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR'],
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
        'spyre.spyrelets.freqSweep_spyrelet.Sweep',
        {'analyzer': 'analyzer','source': 'source'}, 
        {}
    ],

}