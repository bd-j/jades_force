#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, time
import numpy as np
#import matplotlib.pyplot as pl
import logging
import h5py

# child side
from jades_patch import JadesPatch
from forcepho.proposal import Proposer
from forcepho.model import GPUPosterior

# parent side
from dispatcher import SuperScene

logging.basicConfig(level=logging.DEBUG)


def make_imset(out, paths, name, arrs):
    for i, epath in enumerate(paths):
        try:
            g = out[epath]
        except(KeyError):
            g = out.create_group(epath)

        try:
            g.create_dataset(name, data=np.array(arrs[i]))
        except:
            print("Could not make {}/{} dataset from {}".format(epath, name, arrs[i]))


def dump_to_h5(filename, patch, active, fixed,
               pixeldatadict={}, otherdatadict={}):
    pix = ["xpix", "ypix", "ierr"]
    meta = ["D", "CW", "crpix", "crval"]
    with h5py.File(filename, "w") as out:

        out.create_dataset("epaths", data=np.array(patch.epaths, dtype="S"))
        out.create_dataset("bandlist", data=np.array(patch.bandlist, dtype="S"))
        out.create_dataset("exposure_start", data=patch.exposure_start)
        
        for band in patch.bandlist:
            g = out.create_group(band)

        for a in pix:
            arr = getattr(patch, a)
            pdat = np.split(arr, np.cumsum(patch.exposure_N)[:-1])
            make_imset(out, patch.epaths, a, pdat)

        for a in meta:
            arr = getattr(patch, a)
            make_imset(out, patch.epaths, a, arr)

        for a, pdat in pixeldatadict.items():
            make_imset(out, patch.epaths, a, pdat)

        for a, arr in otherdatadict.items():
            out.create_dataset(a, data=arr)

        out.create_dataset("active", data=active)
        out.create_dataset("fixed", data=fixed)


if __name__ == "__main__":


    from config import config
    logger = logging.getLogger(__name__)

    # Build ingredients (parent and child sides)
    sceneDB = SuperScene(config.initial_catalog,
                         maxactive_per_patch=config.maxactive_per_patch)
    logger.info("Made SceneDB")
    patcher = JadesPatch(metastore=config.metastorefile,
                         psfstore=config.psfstorefile,
                         pixelstore=config.pixelstorefile,
                         splinedata=config.splinedatafile)
    logger.info("Made patch")

    # checkout region (parent operation)
    # seed_index = 444  # good source to build a scene from
    region, active, fixed = sceneDB.checkout_region()
    logger.info("checked out scene with {} active sources".format(len(active)))
    sr, sid, ra, dec = region.radius*3600, active[0]["source_index"], region.ra, region.dec
    logger.info("scene of radius {:3.2f} arcsec centered on source {} at (ra, dec)=({}, {})".format(sr, sid, ra, dec))

    # Build patch on CPU side (child operation)
    # Note this is the *fixed* source metadata
    patcher.build_patch(region, fixed, allbands=config.bandlist)
    logger.info("built patch with {} fixed sources".format(len(fixed)))
    logger.info("Patch has {} pixels".format(len(patcher.data)))
    original = np.split(patcher.data, np.cumsum(patcher.exposure_N)[:-1])
    prop_fixed = patcher.scene.get_proposal()
    logger.info("got fixed proposal vector")

    # Send patch to GPU (with fixed sources)
    patcher.return_residual = True
    logger.info("Sending to gpu....")
    gpu_patch = patcher.send_to_gpu()
    logger.info("Initial Patch sent")

    # Evaluate (and subtract) fixed sources
    logger.info("Making proposer and sending fixed proposal")
    proposer = Proposer(patcher)
    out = proposer.evaluate_proposal(prop_fixed)
    fixed_residual = out[-1]
    logger.info("Fixed sources subtracted")

    # Build active patch
    logger.info("Replacing cpu metadata with active sources")
    patcher.pack_meta(active)
    #print(patcher.scene)
    p0 = patcher.scene.get_all_source_params().copy()
    logger.info("got active parameter vector")

    logger.info("Swapping fixed/active metadata and residual/data on GPU")
    patcher.swap_on_gpu()

    # --- Instantiate the ln-likelihood object ---
    # This object reformats the Proposer return and splits the lnlike_function
    # into two, since that computes both lnp and lnp_grad, and we need to wrap
    # them in separate theano ops.
    proposer = Proposer(patcher)
    model = GPUPosterior(proposer, patcher.scene, verbose=verbose)
    logger.info("Built posterior model")

    # run the pymc sampling
    model.proposer.patch.return_residuals = False
    logl = LogLikeWithGrad(model)
    logger.info("Built loglike object")

    model.scene.set_all_parameters(p0)
    pnames = model.scene.parameter_names
    start = dict(zip(pnames, p0))

    with pm.Model() as opmodel:
        # set priors for each element of theta
        z0, _ = prior_bounds(model.scene)
        logger.info("got priors")
        theta = tt.as_tensor_variable(z0)
        # instantiate target density and start sampling.
        pm.DensityDist('likelihood', lambda v: logl(v), observed={'v': theta})
        trace = pm.sample(draws=config.n_iter,
                          tune=config.n_warm,
                          start=start,
                          cores=1, progressbar=False,
                          discard_tuned_samples=True)
    logger.infor("Done sampling")

    chain = np.array([trace.get_values(n) for n in pnames]).T
    model.scene.set_all_parameters(chain[-1, :])
    prop_last = model.scene.get_proposal()
    model.proposer.patch.return_residuals = True
    out = proposer.evaluate_proposal(prop_last)

    pixr = {"data": original,
            "fixed_residual": np.array(fixed_residual),
            "active_residual": np.array(out[-1]),
            }
    extra = {"active_chi2": out[0],
             "active_grad": out[1],
             "ncall": model.ncall.copy(),
             "chain": chain
             }

    fn = "patch{}_ra{:6.4f}_dec{:6.4f}.h5".format("sample", region.ra, region.dec)
    dump_to_h5(fn, proposer.patch, active, fixed,
               pixeldatadict=pixr, otherdatadict=extra)
    logger.info("wrote patch data to {}".format(fn))

    logger.info("Done")