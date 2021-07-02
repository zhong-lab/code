devices = {
    'sp':[
      'lantz.drivers.princetoninstruments.spectrapro.SpectraPro',
      ['TCPIP::169.254.48.177::12345::SOCKET'], # check the IP address,
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