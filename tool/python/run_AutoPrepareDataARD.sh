#!/bin/bash
#SBATCH --partition=general                         # Name of Partition
#SBATCH --ntasks=100                                # Request 256 CPU cores
#SBATCH --time=12:00:00                              # Job should run for up to 1.5 hours (for example)
#SBATCH --mail-type=ALL                              # Event(s) that triggers email notification (BEGIN,END,FAIL,ALL)
#SBATCH --mail-user=su.ye@uconn.edu             # Destination email address

module purge
module load python/3.5.2 gcc/9.2.0 proj/6.0.0  geos/3.5.0 gdal/3.1.0
python AutoPrepareDataARD.py --source_dir='/scratch/suy20004/h011v009' --out_dir='/scratch/suy20004/h011v009_stack' --parallel_mode='HPC'
