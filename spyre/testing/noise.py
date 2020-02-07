# Device List
devices = {


    'attocube':[
        'lantz.drivers.attocube.ANC350',
        ['']
        {}
    ]
}

# Experiment List
spyrelets = {
    'noise':[
        'spyre.spyrelets.noise_spyrelet.Test',
        { 'attocube': 'attocube'},
        {}
    ],
}