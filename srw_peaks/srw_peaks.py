# coding: utf-8

import re

import bnlcrl.pkcli.simulate
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks_cwt
from tqdm import tqdm

from chx_spectrum import chx_spectrum

# List of By magnetic fields to test:
# magn_field_range = np.linspace(0.5, 1.0, 51)
magn_field_range = [0.51]
columns = ['magn_field', 'energy', 'delta', 'atten']
scan_plan = pd.DataFrame(columns=columns)

for und_by in tqdm(magn_field_range):
    # Calculate the spectrum:
    res_file = 'res_spectrum_und_by_{:.3f}.dat'.format(und_by)
    chx_spectrum(und_by=und_by, ss_fn=res_file)

    # Read the spectrum data:
    x_min = None
    x_max = None
    num = None
    with open(res_file) as f:
        for i in range(10):
            r = f.readline()
            if re.search('Initial Photon Energy', r):
                x_min = float(r.split('#')[1].strip())
            if re.search('Final Photon Energy', r):
                x_max = float(r.split('#')[1].strip())
            if re.search('Number of points vs Photon Energy', r):
                num = int(r.split('#')[1].strip())

    x_values = np.linspace(x_min, x_max, num)
    y_values = np.loadtxt(res_file)

    df = pd.DataFrame({'x_values': x_values, 'y_values': y_values})

    # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.find_peaks_cwt.html
    # https://stackoverflow.com/a/25580682
    idx = find_peaks_cwt(df['y_values'], np.arange(1, 30), noise_perc=0.01)

    # Filter noise:
    idx_filt = idx[np.where(df['y_values'][idx] > df['y_values'].max() * 0.001)[0]]

    # 5th harmonic:
    harm5_idx = idx_filt[2]
    energy_harm5 = df['x_values'][harm5_idx]
    intensity_harm5 = df['y_values'][harm5_idx]
    tqdm.write('''
        Harmonic index: {}
        Energy        : {}
        Intensity     : {}
    '''.format(harm5_idx, energy_harm5, intensity_harm5))

    plot = True
    if plot:
        plt.figure()
        plt.plot(df['x_values'], df['y_values'])
        plt.scatter(df['x_values'][idx_filt], df['y_values'][idx_filt])
        plt.xlim (0, x_max)
        plt.ylim (0, 1.1*y_values.max())
        # for i in idx:
        #     print('x: {}    ymax: {}'.format(df['x_values'][i], df['y_values'][i]))
        #     plt.vlines(x=df['x_values'][i], ymin=0, ymax=df['y_values'][i], color='red')
        plt.scatter(df['x_values'][harm5_idx], df['y_values'][harm5_idx], s=200, color='green')
        plt.title('Harmonic #5 index: {}  Energy: {}\nIntensity: {}'.format(harm5_idx, energy_harm5, intensity_harm5))
        plt.xlabel('Energy [eV]')
        plt.xlabel('Intensity [ph/s/.1%bw/mm^2]')
        plt.savefig('{}.png'.format(res_file))


    # Find refractive index decrement and attenuation length for found energy
    # Index of refraction:
    delta_dict = bnlcrl.pkcli.simulate.find_delta(energy=energy_harm5, formula='Be', characteristic='delta', data_file='Be_delta.dat')
    # print(delta_dict)
    delta = delta_dict['characteristic_value']

    # ### Attenuation length:
    atten_dict = bnlcrl.pkcli.simulate.find_delta(energy=energy_harm5, formula='Be', characteristic='atten', data_file='Be_atten.dat')
    # print(atten_dict)
    atten = atten_dict['characteristic_value']

    scan_plan = scan_plan.append({
        'magn_field': und_by,
        'energy': energy_harm5,
        'delta': delta,
        'atten': atten,
    }, ignore_index=True)

print('\n\n')
print(scan_plan)
# scan_plan.to_csv('scan_plan.csv')
scan_plan.to_json('scan_plan.json')
