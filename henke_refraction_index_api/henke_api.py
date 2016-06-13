#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Get Index of Refraction from http://henke.lbl.gov/optical_constants/getdb2.html.
Author: Maksim Rakitin (BNL)
2016
"""

import requests

from console_utils import convert_types, defaults_file, read_json

DEFAULTS_FILE = defaults_file()


class Delta:
    def __init__(self, **kwargs):
        # Get input variables:
        d = read_json(DEFAULTS_FILE)

        self.defaults = d['defaults']
        self.parameters = convert_types(d['parameters'])

        for key, default_val in self.parameters.items():
            if key in kwargs.keys():
                setattr(self, key, kwargs[key])
            elif not hasattr(self, key) or getattr(self, key) is None:
                setattr(self, key, default_val['default'])

        self.delta = None
        self.closest_energy = None
        self.data_file = None
        self.content = None

        self._get_file_name()
        self._get_file_content()
        self._find_delta()

        self.print_info()

    def print_info(self):
        print('Found delta={} for the closest energy={} eV.'.format(self.delta, self.closest_energy))

    def _find_delta(self):
        skiprows = 2
        energy_column = 0
        delta_column = 1
        error_msg = 'Error! Use energy range from {} to {} eV.'
        if self.use_numpy:
            if self.data_file:
                import numpy as np
                data = np.loadtxt(self.data_file, skiprows=skiprows)
                try:
                    idx_previous = np.where(data[:, energy_column] <= self.energy)[0][-1]
                    idx_next = np.where(data[:, energy_column] > self.energy)[0][0]
                except IndexError:
                    raise Exception(error_msg.format(data[0, energy_column], data[-1, energy_column]))

                idx = idx_previous if abs(data[idx_previous, energy_column] - self.energy) <= abs(
                    data[idx_next, energy_column] - self.energy) else idx_next

                self.delta = data[idx][delta_column]
                self.closest_energy = data[idx][energy_column]
            else:
                raise Exception('Processing with NumPy is only possible with the specified file, not content.')
        else:
            if not self.content:
                with open(self.data_file, 'r') as f:
                    self.content = f.readlines()
            else:
                if type(self.content) != list:
                    self.content = self.content.strip().split('\n')
            energies = []
            deltas = []
            for i in range(skiprows, len(self.content)):
                energies.append(float(self.content[i].split()[energy_column]))
                deltas.append(float(self.content[i].split()[delta_column]))
            indices_previous = []
            indices_next = []
            try:
                for i in range(len(energies)):
                    if energies[i] <= self.energy:
                        indices_previous.append(i)
                    else:
                        indices_next.append(i)
                idx_previous = indices_previous[-1]
                idx_next = indices_next[0]
            except IndexError:
                raise Exception(error_msg.format(energies[0], energies[-1]))

            idx = idx_previous if abs(energies[idx_previous] - self.energy) <= abs(
                energies[idx_next] - self.energy) else idx_next

            self.delta = deltas[idx]
            self.closest_energy = energies[idx]

    def _get_file_content(self):
        get_url = '{}{}'.format(self.defaults['server'], self.file_name)
        r = requests.get(get_url)
        self.content = r.text

    def _get_file_name(self):
        if self.precise:
            e_min = self.energy - 1.0
            e_max = self.energy + 1.0
        else:
            e_min = self.e_min
            e_max = self.e_max
        payload = {
            'Density': -1,
            'Formula': self.formula,
            'Material': 'Enter Formula',
            'Min': e_min,
            'Max': e_max,
            'Npts': self.n_points,
            'Output': 'Text File',
            'Scan': 'Energy',
        }
        r = requests.post('{}{}'.format(self.defaults['server'], self.defaults['post_url']), payload)
        content = r.text

        # The file name should be something like '/tmp/xray2565.dat':
        try:
            self.file_name = str(content.split('URL=')[1].split('>')[0].replace('"', ''))
        except:
            raise Exception('\n\nFile name cannot be found! Server response:\n<{}>'.format(content.strip()))
