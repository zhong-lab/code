Creating Spyrelet
=================

To create your own spyrelet, first make a config file.
Pick any config file in ~/code/spyre/testing, and copy the contents into a new file.
Then change the device list so it reflects what devices you will connect to, and change the experiment list to reflect the spyrelet you will use. Finally, name this config file expname.py, where "expname" should be replaced by the name of your experiment.

Then, make the spyrelet itself. Copy template_spyrelet into a new file, and name is expname_spyrelet.py, where "expname" should be replaced by the name of your experiment. _spyrelet is added at the end to distinguish the spyrelet from the config file. 