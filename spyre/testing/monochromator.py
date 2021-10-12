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
    ],
    'sp':[
      'lantz.drivers.princetoninstruments.spectrapro.SpectraPro',
<<<<<<< HEAD
      ['TCPIP::205.208.56.217::12345::SOCKET'], # check the IP address,
=======
      ['TCPIP::<IP Address>::12345::SOCKET'], # check the IP address,
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
      {}
    ]
}

# Experiment List
spyrelets = {
    'spectroscopy_cwicker':[
<<<<<<< HEAD
        'spyre.spyrelets.monochromator_spyrelet.MonochromatorSpyrelet',
=======
        'spyre.spyrelets.spectroscopy_cwicker_spyrelet.PLThinFilm',
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
        {
            'fungen': 'fungen',
            'wm':'wm',
            'SRS':'SRS',
            'sp':'sp',
        },
        {}
    ],
<<<<<<< HEAD
}
=======
}
>>>>>>> 6aaa88ed54b1098234fc40753aab9fe4af5e562d
