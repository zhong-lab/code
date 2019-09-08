##Config file for plthinfilm_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
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
        {'wm':'wm'},
        #,'srs':'srs'}, 
        {}
    ],

}