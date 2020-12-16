# -*- coding: utf-8 -*-
"""
    lantz.drivers.tektronix
    ~~~~~~~~~~~~~~~~~~~~~~~

    :company: Tektronix.
    :description: Test and Measurement Equipment.
    :website: http://www.tek.com/

    ---

    :copyright: 2015 by Lantz Authors, see AUTHORS for more details.
    :license: BSD,

"""

from .tds2024b import TDS2024B
from .tds1012 import TDS1012
from .tds1002b import TDS1002b
from .awg5000 import AWG5000, AWGState
from .tds2024c import TDS2024C

__all__ = ['TDS2024B', 'TDS1002b', 'TDS1012', 'AWG5000', 'TDS2024C']
