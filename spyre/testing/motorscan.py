enable_restore_geometry=True

devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ],
    'osc':[
        'lantz.drivers.tektronix.tds2024c.TDS2024C',
        ['USB0::0x0699::0x03A6::C030873::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'heterodyneecho':[
        'spyre.spyrelets.motorscan_spyrelet.MotorScan',
        {'fungen': 'fungen','osc':'osc'}, 
        {}
    ],

}