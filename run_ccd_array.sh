#!/bin/bash
#SBATCH --partition general
#SBATCH --ntasks 1
#SBATCH --array 1-393

module purge
module load gsl/2.4 gcc/5.4.0-alt zlib/1.2.11 java/1.8.0_162 mpi/openmpi/3.1.3
mpirun ./ccd 
#The variable $SLURM_ARRAY_TASK_MAX is the ID for the last task. 
if [[ $SLURM_ARRAY_TASK_ID == $SLURM_ARRAY_TASK_MIN ]]; then 
	position="first" 
elif [[ $SLURM_ARRAY_TASK_ID == $SLURM_ARRAY_TASK_MAX ]]; then 
	position="last" 
else 
	position="neither" 
fi

#The variable $SLURM_ARRAY_JOB_ID is the ID for the entire array job
#The variable $SLURM_JOB_ID is the ID for each job in the array 
echo "Array Job ID: $SLURM_ARRAY_JOB_ID"
echo "Job ID: $SLURM_JOB_ID" 
echo "Task ID: $SLURM_ARRAY_TASK_ID" 
echo "First or last: $position"
