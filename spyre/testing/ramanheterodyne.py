
# Device List
devices = {
    'vna':[
        'lantz.drivers.VNA.E5071B',
        ['TCPIP0::169.254.137.9::inst0::INSTR'],
        {}
    ],
    'delaygen':[
        'lantz.drivers.stanford.DG645',
        ['TCPIP0::169.254.29.167::inst0::INSTR'],
        {}
    ]    
}

# Experiment List
spyrelets = {
    'vna':[
        'spyre.spyrelets.RamanHeterodyne.Record',
        {'vna': 'vna','delaygen': 'delaygen'}, 
        {}
    ]
}