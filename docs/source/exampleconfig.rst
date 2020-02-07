.. _config:

Dark Count Config File
========================
Every spyrelet needs a corresponding config file in ~/code/spyre/testing.
A config file looks like this:

.. code-block:: python

	# Device List
	devices = {
    	'srs':[
        	'lantz.drivers.stanford.srs900.SRS900',
        	['GPIB0::2::INSTR'],
        	{}
    	]
	}

	# Experiment List
	spyrelets = {
    	'darkcount':[
        	'spyre.spyrelets.darkcount_spyrelet.DarkCount',
        	{'srs': 'srs'},
        	{}
    	],
	}

It has two parts, the device list and experiment list.
The device list should have all instruments listed, with the exception of instruments not connected through NI Visa (QuTAG, Attocube, etc.)
Each instrument should have its lantz driver location and NI Visa address listed.

The experiment list should have the list of spyrelets listed. You can have multiple spyrelets running at once. The spyrelets, like the device list, should have its spyrelet location listed. The instruments should also be listed.