
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
    'lockin':[
        'spyre.spyrelets.lockin_spyrelet_single_deviation.Record',
        {'lockin': 'lockin','source': 'source'},
        {}
    ],

}