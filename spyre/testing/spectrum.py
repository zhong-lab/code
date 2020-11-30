
# Device List
devices = {
    'spa':[
        'lantz.drivers.anritsu.MS2721B',
        ['TCPIP0::169.254.51.199::inst0::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'spectrum':[
        'spyre.spyrelets.spectrumanalyzer.SpectrumAnalyzer',
        {'spa': 'spa'}, 
        {}
    ]
}