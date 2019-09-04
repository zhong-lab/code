##Config file for plthinfilm_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['USB0::0x0957::0x5707::MY53801461::INSTR'],
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],
    'dg':[
        'lantz.drivers.SRS.dg645.DG645',
        ['TCPIP0::169.254.29.167::inst0::INSTR'],
        {}
    ]
    
    # 'srs':[
    #     'lantz.drivers.stanford.srs900.SRS900',
    #     ['GPIB0::2::INSTR'],
    #     {}
    #     ]
}

# Experiment List
spyrelets = {
    'plthinfilm':[
        'spyre.spyrelets.plthinfilm_spyrelet.PLThinFilm',
        {'fungen': 'fungen', 'wm':'wm', 'dg':'dg'},
        #,'srs':'srs'}, 
        {}
    ],

}