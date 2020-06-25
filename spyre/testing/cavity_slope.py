
# Device List
devices = {
    'lockin':[
        'lantz.drivers.lockin.SR865A',
        ['GPIB2::4::INSTR'],
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
    'cavity_slope':[
        'spyre.spyrelets.cavity_slope_spyrelet.Record',
        {'lockin': 'lockin','source': 'source'},
        {}
    ],

}