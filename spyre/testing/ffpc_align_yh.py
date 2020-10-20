# Device List
devices = {
    'osc':[
        'lantz.drivers.tektronix.tds2024c.TDS2024C',
        ['USB0::0x1313::0x8078::P0019269::INSTR'],
        {}
    ]
}
# Experiment List
spyrelets = {ax
    'align':[
        'spyre.spyrelets.ffpc_align_yh_spyrelet.ALIGNMENT',
        {'osc':'osc'},
        {}
    ],

}