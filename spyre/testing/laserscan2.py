# Device List
devices = {
	
	# delete if not using power meter
	'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0022812::INSTR'],
        {}
    ]
    

}
# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan2_spyrelet.LaserScan',
        {
        'pmd': 'pmd'
        }, 
        {}
    ],

}