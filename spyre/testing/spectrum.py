
# Device List
devices = {
    'spa':[
        'lantz.drivers.anritsu.MS2721B',
        ['USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR'],
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
