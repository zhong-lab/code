
# Device List
devices = {
    'lockin':[
        'lantz.drivers.lockin.SR865A',
        ['GPIB1::4::INSTR'],
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
    'lockin':[
        'spyre.spyrelets.lockin_spyrelet.Record',
        {'lockin': 'lockin','source': 'source'},
        {}
    ],

}