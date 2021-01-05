devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'],
        {}
    ],
    'osc':[
        'lantz.drivers.tektronix.tds5104.TDS5104',
        ['GPIB1::15::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'heterodyneecho':[
        'spyre.spyrelets.hole_burn_YSO_spyrelet.Holeburing',
        {'fungen': 'fungen','osc':'osc'}, 
        {}
    ],

}