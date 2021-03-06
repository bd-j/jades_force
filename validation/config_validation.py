#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""config.py - Example configuration script for forcepho runs.
"""

import os
import numpy as np
from argparse import Namespace
config = Namespace()

# -----------
# --- Overall ----
config.logging = True

# -----------------------
# --- Filters being run ---
config.bandlist = ["F42fake"]

# -----------------------
# --- Data locations ---
config.store_name = "galsim_v0"
config.splinedatafile = "stores/sersic_mog_model.smooth=0.0150.h5"
#config.store_directory = os.path.expandvars("$HOME/Projects/jades_force/validation/stores/")
#config.frames_directory = os.path.expandvars("$HOME/Projects/jades_force/data/galsim/")
#config.raw_catalog = os.path.expandvars("$HOME/Projects/jades_force/data/galsim/galsim_xy.dat")
#config.initial_catalog = os.path.expandvars("$HOME/Projects/jades_force/data/galsim/galsim_rectified.fits")

config.store_directory = os.path.expandvars("$SCRATCH/eisenstein_lab/bdjohnson/jades_force/validation/stores/")
config.frames_directory = os.path.expandvars("$SCRATCH/eisenstein_lab/bdjohnson/jades_force/data/galsim/")
config.raw_catalog = os.path.expandvars("$SCRATCH/eisenstein_lab/bdjohnson/jades_force/data/galsim/galsim_xy.dat")
config.initial_catalog = os.path.expandvars("$SCRATCH/eisenstein_lab/bdjohnson/jades_force/data/galsim/galsim_rectified.fits")

sd, sn = config.store_directory, config.store_name
config.pixelstorefile = "{}/pixels_{}.h5".format(sd, sn)
config.metastorefile = "{}/meta_{}.dat".format(sd, sn)
config.psfstorefile = "{}/psf_{}.dat".format(sd, sn)


# ------------------------
# --- Data Types/Sizes ---
config.pix_dtype = np.float32
config.meta_dtype = np.float32
config.super_pixel_size = 8      # number of pixels along one side of a superpixel
config.nside_full = np.array([640, 640])         # number of pixels along one side of a square input frame

# -----------------------
# --- Patch Generation ---
config.max_active_fraction = 0.1
config.maxactive_per_patch = 20

# -----------------------
# --- HMC parameters ---
config.n_warm = 250
config.n_iter = 100
config.n_tune = 100

# ------------------------
# --- PSF information ----
# Used for building PSF store
config.mixture_directory = "/Users/bjohnson/Projects/jades_force/data/psf/mixtures"
config.psf_fwhm = [2.0]  # single gaussian with FWHM = 2 pixels
config.psf_amp = [1.0]
