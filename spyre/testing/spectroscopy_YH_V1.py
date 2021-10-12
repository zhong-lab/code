<<<<<<< HEAD
<<<<<<< HEAD
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
  # 'source':[
  #       'lantz.drivers.agilent.N5181A.N5181A',
  #       ['GPIB1::19::INSTR'], # connecting function generator with ethernet works better for Arb mode
  #       {}
  #   ],    
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],
    'SRS':[
        'lantz.drivers.stanford.srs900.SRS900',
        ['GPIB0::2::INSTR'],   ##SRS - power suppy for the SNSPD
        {}
    ],
    'windfreak':[
        'lantz.drivers.windfreak.synthnvpro.SynthNVPro',
        ['ASRL3::INSTR'], # connecting windfreak, the port number could change time to time
        {}
    ],
}

# Experiment List
spyrelets = {
    'spectroscopy_YH_V1':[
        'spyre.spyrelets.spectroscopy_YH_V1_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
            'SRS':'SRS',
            # 'source':'source'
            'windfreak':'windfreak',
        }, 
        {}
    ],
=======
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],
    'SRS':[
        'lantz.drivers.stanford.srs900.SRS900',
        ['GPIB0::2::INSTR'],   ##SRS - power suppy for the SNSPD
        {}
    ]
}

# Experiment List
spyrelets = {
    'spectroscopy_YH_V1':[
        'spyre.spyrelets.spectroscopy_YH_V1_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
            'SRS':'SRS',
        }, 
        {}
    ],
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
=======
devices = {
    'fungen':[
        'lantz.drivers.keysight.Keysight_33622A.Keysight_33622A',
        ['TCPIP0::A-33622A-01461.local::inst0::INSTR'], # connecting function generator with ethernet works better for Arb mode
        {}
    ],
    'wm':[
        'lantz.drivers.bristol.bristol771.Bristol_771',
        [6535],
        {}
    ],
    'SRS':[
        'lantz.drivers.stanford.srs900.SRS900',
        ['GPIB0::2::INSTR'],   ##SRS - power suppy for the SNSPD
        {}
    ]
}

# Experiment List
spyrelets = {
    'spectroscopy_YH_V1':[
        'spyre.spyrelets.spectroscopy_YH_V1_spyrelet.PLThinFilm',
        {
            'fungen': 'fungen',
            'wm':'wm',
            'SRS':'SRS',
        }, 
        {}
    ],
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
}