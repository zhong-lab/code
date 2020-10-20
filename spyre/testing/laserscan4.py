devices = {
    'osc':[
        'lantz.drivers.tektronix.tds5104.TDS5104',
        ['GPIB1::15::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan4_spyrelet.LaserScan',
        {'osc':'osc'}, 
        {}
    ],

}