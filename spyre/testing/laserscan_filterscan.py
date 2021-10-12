devices = {

    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],

    'tf':[
        'lantz.drivers.santec.otf930.OTF930',
        ['GPIB2::17::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan_filterscan_spyrelet.LaserScan',
        {   'wm':'wm',
            'tf':'tf'
        },
        {}
    ],

}