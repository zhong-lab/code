devices = {
    'sp':[
      'lantz.drivers.princetoninstruments.spectrapro.SpectraPro',
      ['TCPIP::205.208.56.217::12345::SOCKET'], # check the IP address,
      {}
    ]
}

# Experiment List
spyrelets = {
    'spectroscopy_cwicker':[
        'spyre.spyrelets.monochromatortest_spyrelet.MonochromatorSpyrelet',
        {
            'sp':'sp',
        },
        {}
    ],
}