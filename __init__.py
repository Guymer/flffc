"""
Find Location Furthest From Coast (FLFFC)

This Python 3.x module contains all the functions required to calculate the
location that is the furthest away from the coast in a particular country. It
also contains a wrapper function to perform the job for you.
"""

# Import standard modules ...
import sys

# Import sub-functions ...
from .run import run

# Ensure that this module is only imported by Python 3.x ...
if sys.version_info.major != 3:
    raise Exception("the Python module \"flffc\" must only be used with Python 3.x")
