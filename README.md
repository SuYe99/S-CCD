# SCCD

# Stochastic Continuous Change Detection (V0.4)
### Authors: Su Ye, John Rogan and Zhe Zhu
#### Maintainer: Su Ye (remotesensingsuy@gmail.com)
History
- Version 0.4: S-CCD paper (10/10/2020); supporting both HPC and Desktop environment; adding python interface; fixed numerous discrepancies with matlab COLD
- Version 0.3: replace all openmp functions with mpi functions (06/17/2019)
- Version 0.2: Put two non-lasso bands back for modeling; fixed some bugs (05/16/2019)
- Version 0.1: Original development (11/27/2018)

S-CCD exists to provide an efficient implementation of S-CCD and COLD algorithm 

(The current version was only tested in Ubuntu 18.04, macOS10.14 and HPC environment)

## 1. Pre-work: clone github repo to your local directory
### 1.1 Clone or pull the latest SCCD git repo 
### 1.2 Download Landsat ARD images 
Go to [EarthExplorer](https://earthexplorer.usgs.gov/), and download all Landsat ARD images for your tile into YOUR_TAR_DIRECTORY  
### 1.3 Install dependencies

(Ubuntu)
```
sudo apt-get install build-essential
sudo apt-get install libgsl-dev
sudo apt-get install gfortran
```
(MAC)
```
brew install gsl
brew install gcc
```

## 2. Prepare ENVI format of Landsat image in parallel 
S-CCD required an additional step of converting original Landsat tiff to ENVI format. We already tested this approach v.s. processing original tiff. This approach can be 7 times faster. To get through this step, you require ~500 GB space in your local computer or HPC, and python or CCDC Assistor installed.

### 2.1 Set up python environment using conda
```
cd /YOUR_SCCD_DIRECTORY/S-CCD/tool/python
conda create -n sccdenv python=3.6 # create a new environmnet
conda activate sccdenv
conda install --file=requirements.txt # install required packages
```
### 2.2 Preparing ENVI format landsat dataset
```
python AutoPrepareDataARD.py --source_dir=YOUR_TAR_DIRECTORY --out_dir=YOUR_ENVI_DIRECTORY
```
Note 1: you can specify threshold for percentage of clear pixels to eliminate heavy cloud-contaminated scene. For details, please run for other supporting inputted parameters 
```
python AutoPrepareDataARD.py --help
```
Note 2: for matlab users, this step can be substituted by using MATLAB-based CCDC Assistor which can be downloaded https://github.com/GERSL/CCDC

## 3. Run S-CCD/COLD
### 3.1 For python desktop users:
#### 3.1.1 Compile c and cython files
cd to the main directory of sccd package and run procedure file
```
cd /YOUR_SCCD_DIRECTORY/S-CCD
./compilation_procedure 
```
Just ignore the warning messages, and if successful, you can find two executable files called 'libsccd.so' and 'pysccd.cython-36m-darwin.so' (this name is for mac; it might be different affix under different system) in the directory /YOUR_SCCD_DIRECTORY/S-CCD/tool/python

#### 3.1.2 Copy executable files into your python project directory
Copy pysccd.cython-36m-darwin.so and libsccd.so into your python project directory, and try the below python code line under your python project directory
```python
import pysccd
```
Note: for Ubuntu system, you may also need to copy these two to the folder of your conda package directory.
If no error message, then you should be ready to go.
#### 3.1.3 CSV-based processing
S-CCD package supports four processing modes: 1) single pixel; 2) single scanline; 3) tile-based processing; 4) csv-based processing.
It is recommended to use CSV-based processing to make a quick testing on the S-CCD package for the first time. Please check the sample script '/YOUR_SCCD_DIRECTORY/S-CCD/python/csvbased_example.py' for processing a plot-based spectral time series in /YOUR_SCCD_DIRECTORY/S-CCD/test/spectral_344_3964_obs.csv. Please change Line 14 and 15 in csvbased_example.py to your own directory, and run. If successful, you will see the continuous changes of three states as S-CCD model each component as stochastic process, and breakpoint detected by S-CCD associated with West Fork fire highlighted as black as
![S-CCD-sample-result](https://github.com/SuYe99/S-CCD/tree/devel/test/spectral_336_3980_obs.png)
How to make your own csv? Please see Q&A at the end.
#### 3.1.4 Single-pixel/single-scanline processing
You can also run single-pixel processing by inputing column and row number for your interested location for a Landsat ARD tile, after the ENVI image folders were produced by AutoPrepareDataARD.py. An example to run and visualize result can be seen as in /YOUR_SCCD_DIRECTORY/S-CCD/python/singlepixel_example.py
#### 3.1.5 Tile-based processing
Please take reference on /YOUR_SCCD_DIRECTORY/S-CCD/python/tilebased_processing.py as example.

#### 3.1.6 COLD algorithm
This package also provides C-based implementation for COLD algorithm. Please use /YOUR_SCCD_DIRECTORY/S-CCD/python/csvbased_example_COLD.py as example.To switch from S-CCD to COLD, just simply change the corresponding inputted parameter for 'py_sccd' function, i.e., 'method', from '2' to '1'.
Note: one discrepancy between C-implemented and MATLAB-implment COLD is that the ordinal dates outputed by two packages are 366 day offset. The reason is that Matlab counts the first day as '01-01-0000', while C version counts the first day as '01-01-0001' which aligned with 'fromordinal' and 'toordinal' python function 

### 3.2 Run S-CCD without python under desktop environment
#### 3.2.1 Compile package:
```
cd /YOUR_SCCD_DIRECTORY/S-CCD
make -f Makefile_exe
make -f Makefile_exe install
```

#### 3.2.2 Run the exe through command line
```
cd /YOUR_SCCD_DIRECTORY/S-CCD/bin
vi variables_desktop # control your input, output, algorithm, parameters as you needed
./ccd variables_desktop
```
#### 3.2.3 Clean .o and exe
```
cd /YOUR_SCCD_DIRECTORY/S-CCD
make -f Makefile_exe clean
```
### 3.3 Run S-CCD program under HPC environment
Download the newest S-CCD repo
```
cd /YOUR_SCCD_DIRECTORY/S-CCD
make -f Makefile_hpc
make -f Makefile_hpc install
```
Then change variables /YOUR_SCCD_DIRECTORY/S-CCD/bin/variables and hpc configuration files /YOUR_SCCD_DIRECTORY/S-CCD/bin/variables/run_ccd.sh. For example, if you want to request 300 cores for parallel, please update '#SBATCH --ntasks=300' in 'run_ccd.sh'. Then submit your task 
```
sbatch run_ccd.sh
```

## Q&A
##### Q1: "cannot find -lz" error
A: try installing lz dependency using the below comand line 
(for ubuntu users)
```
sudo apt-get install zlib1g-dev
```
##### Q2: Errors related to 'GSL_SCI_INC' and 'GSL_SCI_LIB' 
A: you may need to try modifying 'GSL_SCI_INC' and 'GSL_SCI_LIB' in '/YOUR_SCCD_DIRECTORY/S-CCD/Makefile' and point them to the directory of your own machine. 

##### Q3: can I make my own csv as plot-based data for input?
A: Yes, S-CCD supports users to input your own csv for plot-based landsat data, which you can extract from other database such as GEE, AWS. 
When you generated your own CSV, please follows the column order as 'blue, green, red, nir, SWIR1, SWIR2, brightness temperature, cloudmask, sensor'. For 'cloudmask' column, please check the definition in defines.h.
```c
#define CFMASK_CLEAR   0
#define CFMASK_WATER   1
#define CFMASK_SHADOW  2
#define CFMASK_SNOW    3
#define CFMASK_CLOUD   4
#define CFMASK_FILL  255
#define IMAGE_FILL -9999
```
For 'sensor' column, it is not useful at current stage (we remained it for future development). You can assign random values to this column  
