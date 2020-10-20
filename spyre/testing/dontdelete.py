devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'holeburning':[
        'spyre.spyrelets.DONTDELETE_spyrelet.DontDelete',
        {'fungen': 'fungen'}, 
        {}
    ],

}