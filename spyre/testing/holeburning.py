devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
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
    'holeburning':[
        'spyre.spyrelets.holeburning_spyrelet.HoleBurning',
        {'fungen': 'fungen','osc':'osc'}, 
        {}
    ],

}