
# Device List
devices = {
    'spa':[
        'lantz.drivers.spectrum.MS2721B',
        ['USB0::0x0B5B::0xFFF9::1118010_150_11::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'save_spectrum':[
        'spyre.spyrelets.save_spectrum_spyrelet.SpectrumAnalyzer',
        {'spa': 'spa'}, 
        {}
    ]
}