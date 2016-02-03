import glob

import numpy as np

from plot_time_interval import plot_time_interval

etalon_dir = 'data_example_10_np=20_etalon'
etalon_file = etalon_dir + '/ex10_res_int_prop_me.dat'
content_etalon = np.loadtxt(etalon_file, skiprows=11)

dirs_list = glob.glob('data_example_10_*')
data = []
for d in dirs_list:
    if d != etalon_dir:
        num_proc = int(d.split('_')[3])
        dat_file = d + '/ex10_res_int_prop_me.dat'
        content = np.loadtxt(dat_file, skiprows=11)
        try:
            # From http://stackoverflow.com/questions/17197492/root-mean-square-error-in-python:
            # First solution:
            '''
            from sklearn.metrics import mean_squared_error
            rms = np.sqrt(mean_squared_error(content, content_etalon))
            '''

            # Second solution:
            N = len(content_etalon)
            rms = np.linalg.norm(content - content_etalon) / np.sqrt(N)

            print('%i  %.3f' % (num_proc, rms))
            data.append([num_proc, rms])
        except:
            print('Cannot calculate RMSE for %i processors. Output .dat file looks to be corrupt.' % num_proc)

plot_time_interval(data, interval=15, number_of_particles=50000)
