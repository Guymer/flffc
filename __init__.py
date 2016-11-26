# -*- coding: utf-8 -*-

"""
Find Location Furthest From Coast (FLFFC)

This module contains all the functions required to calculate the location that
is the furthest away from the coast in a particular country. It also contains a
wrapper function to perform the job for you.
"""

# Load sub-functions ...
from .angle_between_two_locs import angle_between_two_locs
from .dist_between_two_locs import dist_between_two_locs
from .run import run
