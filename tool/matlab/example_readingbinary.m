path = '/media/su/DataFactory/Dissertation_Meta/Landsat/ccdc_result/RUN0/record_change_row1113_col2943.dat';
m = memmapfile(path, 'Format', {'int32',  [1 1] 't_start'; 'int32',  [1 1] 't_end'; 'int32', [1 1] 't_break';
    'single', [8 7]  'coefs'; 'single', [1 7]  'rmse'; 'int32',  [1 1] 'pos';
    'single',  [1 1] 'change_prob'; 'int32', [1 1] 'num_obs'; 'int32', [1 1] 'category'
    'single', [1 7]  'magnitude';});
rec_cg_c = transpose(m.Data)

path = '/home/su/Documents/Jupyter/source/LandsatARD/record_change_row1266_col2388.dat';
m = memmapfile(path, 'Format', {'int32',  [1 1] 't_start'; 'int32',  [1 1] 't_end'; 'int32', [1 1] 't_break';
    'int32', [1 1] 't_stable'; 'single', [6 7]  'coefs'; 'single', [1 7]  'avg_f'; 'single', [1 7]  'obs_disturbance';
    'single', [5 7]  'state_disturbance'; 'single', [1 7]  'rmse'; 'int32',  [1 1] 'pos';
    'int32', [1 1] 'num_obs'; 'int32', [1 1] 'category'
    'single', [1 7]  'magnitude';});
rec_cg_c = transpose(m.Data)

path = '/media/su/LaCie/Tyler/Results/record_change_1188_1278_ccd.dat';
m = memmapfile(path, 'Format', {'int32',  [1 1] 't_start'; 'int32',  [1 1] 't_end'; 'int32', [1 1] 't_break';
    'single', [8 7]  'coefs'; 'single', [1 7]  'rmse'; 'int32',  [1 1] 'pos';
    'single',  [1 1] 'change_prob'; 'int32', [1 1] 'num_obs'; 'int32', [1 1] 'category'
    'single', [1 7]  'magnitude';});
rec_cg_c = transpose(m.Data)

path = '/media/su/LaCie/Tyler/Results/record_change_1188_1278_sccd.dat';
m = memmapfile(path, 'Format', {'int32',  [1 1] 't_start'; 'int32',  [1 1] 't_end'; 'int32', [1 1] 't_break';
    'int32', [1 1] 't_stable'; 'single', [6 7]  'coefs'; 'single', [1 7]  'avg_f'; 'single', [1 7]  'obs_disturbance';
    'single', [5 7]  'state_disturbance'; 'single', [1 7]  'rmse'; 'int32',  [1 1] 'pos';
    'int32', [1 1] 'num_obs'; 'int32', [1 1] 'category'
    'single', [1 7]  'magnitude';});
rec_cg_c_s = transpose(m.Data)

path = '/media/su/LaCie/Tyler/Results/record_change_row578.dat';
m = memmapfile(path, 'Format', {'int32',  [1 1] 't_start'; 'int32',  [1 1] 't_end'; 'int32', [1 1] 't_break';
    'single', [8 7]  'coefs'; 'single', [1 7]  'rmse'; 'int32',  [1 1] 'pos';
    'single',  [1 1] 'change_prob'; 'int32', [1 1] 'num_obs'; 'int32', [1 1] 'category'
    'single', [1 7]  'magnitude';});
rec_cg_c = transpose(m.Data)