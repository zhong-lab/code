
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
    'cavity_noise':[
        'spyre.spyrelets.cavity_noise_spyrelet.Record',
        {'lockin': 'lockin','source': 'source'},
        {}
    ],

}