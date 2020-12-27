##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
    # 'srs':[
    #     'lantz.drivers.stanford.srs900.SRS900',
    #     ['GPIB0::2::INSTR'],
    #     {}
    #     ]
}

# Experiment List
spyrelets = {
    'twopulsephotonecho':[
        'spyre.spyrelets.twopulsephotonecho_spyrelet.TwoPulsePhotonEcho',
        {'fungen': 'fungen'},#,'srs':'srs'}, 
        {}
    ],

}