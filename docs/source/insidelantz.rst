Inside Lantz
============================

Inside the lantz folder, there are a couple of folders and numerous python files.
The drivers folder will be used and modified most frequently, and contains all
intrument-specific lantz drivers. More on this folder in the next section.

The simulators folder has some artificial instruments mainly for tutorial
purposes. These were all created by the original creators of lantz, and their
tutorial online uses the fungen.py as an example.

Testsuite, much like the simulators folder, also contains simulations of
intruments for testing/tutorial purposes. Unlike simulators folder, testsuite
contains instruments that do not communicate via NI-VISA.

UI contains, as the name suggests, user interface scripts that build up the GUI
for lantz. Utils are various utility files, that should generally also not be
altered.

Finally, there are a number of python files. These are all scripts that help
lantz connect to the instrument. These also generally should not be altered.
However, if you fail to connect to the instrument, chances are you may see an
error from one of these files. foreign.py in particular allows connections to
nastier C-based instruments.
