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
    'threepulsephotonecho':[
        'spyre.spyrelets.threepulsephotonecho_spyrelet.ThreePulsePhotonEcho',
        {'fungen': 'fungen'}, 
        {}
    ],

}