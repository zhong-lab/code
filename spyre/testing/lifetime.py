##Config file for lifetime_spyrelet.py in spyre/spyre/spyrelet/

# Device List
devices = {
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ]
}

# Experiment List
spyrelets = {
    'lifetime':[
        'spyre.spyrelets.lifetime_spyrelet.Lifetime',
        {'wm':'wm'}, 
        {}
    ],
}