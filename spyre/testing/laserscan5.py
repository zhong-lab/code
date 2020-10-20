devices = {
    'osc':[
        'lantz.drivers.tektronix.tds2024c.TDS2024C',
        ['USB0::0x0699::0x03A6::C030873::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan5_spyrelet.LaserScan',
        {'osc':'osc'}, 
        {}
    ],

}