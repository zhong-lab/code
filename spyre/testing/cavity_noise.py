
# Device List
devices = {
    'lockin':[
        'lantz.drivers.lockin.SR865A',
        ['GPIB0::4::INSTR'],
        {}
    ],
    'source':[
        'lantz.drivers.mwsource.SynthNVPro',
        ['ASRL8::INSTR'],
        {}
    ]    
}
# Experiment List
spyrelets = {
    'noise':[
        'spyre.spyrelets.cavity_noise_spyrelet.Record',
        {'lockin': 'lockin','source': 'source'},
        {}
    ],

}