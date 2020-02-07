devices = {
    'osc':[
        'lantz.drivers.tektronix.tds5104.TDS5104',
        ['GPIB1::15::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'printscope':[
        'spyre.spyrelets.printscope_spyrelet.PrintScope',
        {'osc':'osc'}, 
        {}
    ],

}