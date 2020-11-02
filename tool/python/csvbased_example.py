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

mode = 4
in_path = '/Users/coloury/Dropbox/Documents/QTProjects/CCDC_C/test/spectral_336_3980_obs.csv'
out_path = '/Users/coloury/Dropbox/Documents/QTProjects/CCDC_C/test'
probability = 0.95
min_days_conse = 80
row = 1 # won't affect the result for csv
col = 1 # won't affect the result for csv
method = 2
user_mask_path = ''
output_mode = 1 # 11: both output; 1: output states; 10: output observation file
bandselection_bit = 62 # the bit value for the default spectral inputs, namely green, red, nir, SWIR1 and SWIR2
sccd_dt = np.dtype([('t_start', np.int32), ('t_end', np.int32), ('t_break', np.int32), ('pos', np.int32), ('num_obs', np.int32),
               ('category', np.int16), ('land_type', np.int16), ('t_confirmed', np.int32), ('change_prob', np.int32),
               ('coef', np.double, (7, 6)), ('obs_disturbance', np.double, (7, 1)),
               ('state_disturbance', np.double, (7, 5)), ('rmse', np.double, (7, 1)), ('magnitude', np.double, (7, 1))])

ret = pysccd.py_sccd(mode, in_path.encode('ascii'), out_path.encode('ascii'), \
                    row, col, method, bandselection_bit, user_mask_path.encode('ascii'),
                     probability, min_days_conse, output_mode=output_mode)

n_b = 5
bn_shortname = 'B' + str(n_b)
if n_b == 1:
    bandname = 'Blue'
elif n_b == 2:
    bandname = 'Green'
elif n_b == 3:
    bandname = 'Red'
elif n_b == 4:
    bandname = 'NIR'
elif n_b == 5:
    bandname = 'SWIR1'
elif n_b == 6:
    bandname = 'SWIR2'
elif n_b == 7:
    bandname = 'BT'

# extract base name
basename = os.path.splitext(os.path.basename(in_path))[0]
ccd_plot = np.fromfile(os.path.join(out_path, basename + '_sccd.dat'), dtype=sccd_dt)

# read state records
plot_state = pd.read_csv(os.path.join(out_path, basename + '_StateRecords_' + bn_shortname + '.csv'), na_values=-9999)
plot_state.columns = ['Dates', 'Trend', 'Annual', 'Semiannual', 'Foutmonth',
                      'obs', 'rmse']
plot_state['predicted'] = plot_state['Trend'] + plot_state['Annual'] +plot_state['Semiannual']
DatesFromOrdinal = [pd.Timestamp.fromordinal(row - 366) for row in plot_state["Dates"]]
plot_state.loc[:,'Dates'] = DatesFromOrdinal

# read obs records
plot_obs = pd.read_csv(in_path)
plot_obs.columns = ['Dates', 'Blue', 'Green', 'Red', 'NIR', \
                    'SWIR1', 'SWIR2', 'BT', 'QA', 'sensor']
plot_obs_clean = plot_obs.loc[plot_obs['QA'] == 0]
DatesFromOrdinal = [pd.Timestamp.fromordinal(row - 366)
                    for row in plot_obs_clean["Dates"]]
plot_obs_clean.loc[:,'Dates'] = DatesFromOrdinal


f, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(12, 8), sharex=True)
#plot_obs_clean = plot_obs_clean[plot_obs_clean['BAND 7'] < 2000]

plot_state['predicted'] = plot_state['Trend'] + plot_state['Annual'] + plot_state['Semiannual']

sns.set(style="darkgrid")
sns.set_context("notebook")

# aim to create a graph which has extra 1/4 total height higher/lower than max/min
# level
extra = (np.max(plot_state['Trend']) - np.min(plot_state['Trend']))/4
ax1.set(ylim=(np.min(plot_state['Trend'])-extra, np.max(plot_state['Trend'])+extra))
sns.lineplot(x="Dates", y="Trend", data=plot_state, ax=ax1, color="blue")

# annual
extra = (np.max(plot_state['Annual']) - np.min(plot_state['Annual']))/4
ax2.set(ylim=(np.min(plot_state['Annual'])-extra, np.max(plot_state['Annual'])+extra))
sns.lineplot(x="Dates", y="Annual", data=plot_state, ax=ax2, color="blue")

# semiannual
extra = (np.max(plot_state['Semiannual']) - np.min(plot_state['Semiannual']))/4
ax3.set(ylim=(np.min(plot_state['Semiannual'])-extra, np.max(plot_state['Semiannual'])+extra))
sns.lineplot(x="Dates", y="Semiannual", data=plot_state, ax=ax3, color="blue")

# actual
extra = (np.max(plot_state['predicted']) - np.min(plot_state['predicted']))/4
ax4.set(ylim=(np.min(plot_state['predicted'])- 4 * extra,
                    np.max(plot_state['predicted'])+ 2 * extra))
sns.lineplot(x="Dates", y="predicted", data=plot_state, label="1-step-ahead pred", ax=ax4, color="m")
ax4.plot('Dates', bandname, 'y+', data=plot_obs_clean, label='Actual')


# plot the break
for i in range(len(ccd_plot) - 1):
    if(ccd_plot[i]['category'] % 10 == 1):
        ax1.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='k')

        ax2.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='k')
        ax3.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='k')
        ax4.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='k')
        ax4.text(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), ax4.get_ylim()[1],
            str(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366).date()),
             transform=ax4.transData)
    else:
        ax1.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='r')
        ax2.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='r')
        ax3.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='r')
        ax4.axvline(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), color='r')
        ax4.text(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366), ax4.get_ylim()[1],
            str(pd.Timestamp.fromordinal(ccd_plot[i]['t_break'] - 366).date()),
             transform=ax4.transData)
