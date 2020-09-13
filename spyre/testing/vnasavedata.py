
# Device List
devices = {
    'vna':[
        'lantz.drivers.VNA.E5071B',
        ['TCPIP0::169.254.137.9::inst0::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'vna':[
        'spyre.spyrelets.vnasavedata.VNASaveData',
        {'vna': 'vna'}, 
        {}
    ]
}