Keysight_33622A.py
^^^^^^^^^^^^^^^^^^^^^
The header of the main driver file looks like this::

    from lantz import Feat, DictFeat, Action
    from lantz.messagebased import MessageBasedDriver
    from lantz.drivers.keysight.arbseq_class import Arbseq_Class
    from time import sleep

    class Keysight_33622A(MessageBasedDriver):

__init__.py
^^^^^^^^^^^
The init file should look something like this::

    from .Keysight_33622A import Keysight_33622A
    from .seqbuild import SeqBuild
    from .arbseq_class import Arbseq_Class

    __all__ = ['Keysight_33622A', 'SeqBuild', 'Arbseq_Class']
