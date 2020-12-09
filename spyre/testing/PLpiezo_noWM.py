devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
}

# Experiment List
spyrelets = {
    'PLpiezo_cwicker':[
        'spyre.spyrelets.PLpiezo_noWM_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen'
        }, 
        {}
    ],

}