# Device List
devices = {
	
	# delete if not using power meter
	'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ]
    

}
# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan6_spyrelet.LaserScan',
        {
        'pmd': 'pmd'
        }, 
        {'wm': 'wm'}
    ],

}