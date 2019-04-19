# -*- coding: utf-8 -*-

"""
Find Location Furthest From Coast (FLFFC)

This module contains all the functions required to calculate the location that
is the furthest away from the coast in a particular country. It also contains a
wrapper function to perform the job for you.
"""

# Ensure that this module is only imported by Python 2.x ...
import sys
if sys.version_info.major != 2:
    raise Exception("the Python module \"flffc\" must only be used with Python 2.x")

# Load sub-functions ...
from .run import run
