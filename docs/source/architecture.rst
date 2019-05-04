Architecture
============

Scaffolding: /code
^^^^^^^^^^^^^^^^^^
The root directory of the entire code base, located in /code, contains 5 main
files: cmder, docs, lantz, pyqtgraph, and spyre. We introduce them here.

cmder
^^^^^^^^^^^^^^^^^^
The cmder folder contains "Cmder.exe", which is the command line console used
to execute spyre. The usual cmd or mingw can be used as well, but Cmder has some
nice colors has the path configured to the spyre conda environment. In general,
apart from running Cmder.exe, this folder should not have to be edited.

docs
^^^^^^^^^^^^^^^^^^
Contains the files that build this documentation. More on this in the section
on creating documentation.

lantz
^^^^^^^^^^^^^^^^^^
Lantz is a Python toolkit that allows communication with scientific instruments
through lantz drivers, and various API. Drivers are instrument-specific, and are
grouped by the company that manufactured each device. Lantz is basically the
glue that holds together Python, Spyre, and device DLLs and drivers.

Extensive documentation on lantz can be found here:

https://lantz.readthedocs.io/en/latest/index.html

pyqtgraph
^^^^^^^^^^^^
Pyqtgraph is just a Python graphing library, and is kept in this particular
location for unknown purposes. One could go through the code and change all
references to pyqtgraph to another, more suitable location (such as a lib folder),
but it's not necessary. Since this is a prewritten library, there should be
no need to edit this folder.

spyre
^^^^^^^^^^^^
Spyre is a toolkit that goes hand in hand with lantz. While lantz establishes
connections with the instrument, spyrelets (which are basically spyre widgets)
are scripts that bring together all the lantz devices to run an experiment.

Spyre also has a build-in GUI that graphs outputs and allows for tuning of
various experimental parameters. Eventually, there will be no need to change
any source code for spyrelets to change experimental parameters.
