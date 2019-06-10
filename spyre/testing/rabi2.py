##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'rabi2':[
        'spyre.spyrelets.rabi2_spyrelet.Rabi2',
        {'fungen': 'fungen'}, 
        {}
    ],

}