#!/bin/bash

#SBATCH -n 1 # Number of cores requested
#SBATCH -N 1 # Ensure that all cores are on one machine
#SBATCH --gres=gpu:1
#SBATCH --mem-per-cpu=1000 # Memory per node in MB (see also --mem-per-cpu)
#SBATCH -p gpu # Partition to submit to
#SBATCH -t 12:00:00 # Runtime
#SBATCH -J force_sample_test
#SBATCH -o /n/holyscratch01/eisenstein_lab/bdjohnson/jades_force/cannon/logs/samplepatch_%A_%a.out # Standard out goes to this file
#SBATCH -e /n/holyscratch01/eisenstein_lab/bdjohnson/jades_force/cannon/logs/samplepatch_%A_%a.err # Standard err goes to this file

module purge
module load intel/19.0.5-fasrc01 openmpi/4.0.1-fasrc01 hdf5/1.10.5-fasrc01
module load cuda/10.1.243-fasrc01
module load Anaconda3/5.0.1-fasrc01

# where code will be run
jdir=${SCRATCH}/eisenstein_lab/bdjohnson/jades_force/cannon/

# Do every 100th galaxy
declare -i idx
idx=${SLURM_ARRAY_TASK_ID}*100


source activate jadespho
cd $jdir
python test_sample.py --logging --seed_index=$idx --outfile=test_sample_idx${idx}.h5