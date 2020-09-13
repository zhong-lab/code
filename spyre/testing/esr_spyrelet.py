
# Device List
devices = {
    'lockin':[
        'lantz.drivers.lockin.SR865A',
        ['GPIB0::4::INSTR'],
        {}
    ],
    'source':[
        'lantz.drivers.keysight.N5181A',
        ['TCPIP0::A-N5181A-41097::inst0::INSTR'],
        {}
    ]    
}
# Experiment List
spyrelets = {
    'esr':[
        'spyre.spyrelets.ESR_Spyrelet.Record',
        {'lockin': 'lockin','source': 'source'},
        {}
    ],

}