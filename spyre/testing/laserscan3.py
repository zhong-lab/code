# Device List
# test comment 
# test comment #2
# test comment #3
# test comment #4
# test comment #5
# test comment #6
# test comment #7
# test comment #8
devices = {

    #'wm':[
    #    'lantz.drivers.bristol.bristol771.Bristol_771',
    #    [6535],
    #    {}
    #],

    'pmd':[
        'lantz.drivers.thorlabs.pm100d.PM100D',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {
    'laserscan':[
        'spyre.spyrelets.laserscan3_spyrelet.LaserScan',
        {'pmd':'pmd'}, 
        {}
    ],

}