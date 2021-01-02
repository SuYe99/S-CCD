# this script show how to run SCCD or COLD from python
import pysccd
import numpy as np
import os
import pandas as pd
import time
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import datetime
from datetime import date

mode = 3
in_path = '/Volumes/Samsung_T5/ENVI_LandsatARD' # please change as needed
out_path = '/Users/coloury/Dropbox/Documents/QTProjects/CCDC_C/test' # please change as needed
n_cores = 8
probability = 0.95
min_days_conse = 80
row = 1000 # not useful for tile processing
col = 1000 # not useful for tile processing
method = 2 # 1 is COLD; 2 is S-CCD
user_mask_path = ''
bandselection_bit = 62 # the bit value for the default spectral inputs, namely green, red, nir, SWIR1 and SWIR2

ret = pysccd.py_sccd(mode, in_path.encode('ascii'), out_path.encode('ascii'), \
                    row, col, method, bandselection_bit, user_mask_path.encode('ascii'),
                     probability, min_days_conse, n_cores=n_cores)
