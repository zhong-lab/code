devices = {
    'osc':[
        'lantz.drivers.tektronix.tds2024c.TDS2024C',
        ['USB0::0x0699::0x03A6::C030873::INSTR'],
        {}
    ]
}

# Experiment List
spyrelets = {
    'scopecapture':[
        'spyre.spyrelets.scopecapture_spyrelet.ScopeCapture',
        {'osc':'osc'}, 
        {}
    ],

}