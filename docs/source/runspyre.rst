.. _runspyre:

Running Spyrelets
=================
To run a written spyrelet, first make sure spyre is activated by looking for (spyre) on the left side of cmd.
If not, activate spyre::

	activate spyre

.. note::
	Sometimes, your path will not be set to envs and the above command will not work. In this case, look for the environment::

		conda list envs

	After finding the path the spyre environment, activate it with "activate" followed by the full path to the spyre env.

If spyre is not installed, refer to :ref:`installcode`.

Navigate to your code path, and go to ~/code/spyre/testing.
To run the spyrelet, (let the spyrelet name be "example")::

	python main.py example

The spyrelet name must be passed into the argument of main.py.