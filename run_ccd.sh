#!/bin/bash
#SBATCH --partition=general                         # Name of Partition
#SBATCH --ntasks=100                                # Request 256 CPU cores
#SBATCH --time=12:00:00                              # Job should run for up to 1.5 hours (for example)
#SBATCH --mail-type=ALL                              # Event(s) that triggers email notification (BEGIN,END,FAIL,ALL)
#SBATCH --mail-user=su.ye@uconn.edu             # Destination email address

module purge
module load gsl/2.4 gcc/5.4.0-alt zlib/1.2.11 java/1.8.0_162 mpi/openmpi/3.1.3 
mpirun ./ccd
