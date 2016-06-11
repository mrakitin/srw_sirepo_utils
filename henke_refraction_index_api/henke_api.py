#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Get Index of Refraction from http://henke.lbl.gov/optical_constants/getdb2.html.
Author: Maksim Rakitin (BNL)
2016
"""
import json
import os

import requests

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))

# Fix for Jython:
try:
    SCRIPT_PATH = SCRIPT_PATH.replace(os.path.join(format(os.environ['HOME']), '.jython-cache/cachedir/classes'), '')
except:
    pass

CONFIG_DIR = os.path.join(SCRIPT_PATH, 'configs')
DEFAULTS_FILE = os.path.join(CONFIG_DIR, 'defaults.json')


class Delta:
    def __init__(self, **kwargs):
        # Get input variables:
        d = _read_json(DEFAULTS_FILE)

        self.defaults = d['defaults']
        self.parameters = _convert_types(d['parameters'])

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


def henke_console():
    import argparse

    data = _read_json(DEFAULTS_FILE)
    description = data['description']
    defaults = _convert_types(data['parameters'])

    # Processing arguments:
    required_args = []
    optional_args = []

    for key in sorted(defaults.keys()):
        if defaults[key]['default'] is None:
            required_args.append(key)
        else:
            optional_args.append(key)

    parser = argparse.ArgumentParser(description=description)

    for key in required_args + optional_args:
        args = []
        if 'short_argument' in defaults[key]:
            args.append('-{}'.format(defaults[key]['short_argument']))
        args.append('--{}'.format(key))

        kwargs = {
            'dest': key,
            'default': defaults[key]['default'],
            'required': False,
            'type': defaults[key]['type'],
            'help': '{}.'.format(defaults[key]['help']),
        }
        if defaults[key]['default'] is None:
            kwargs['required'] = True

        if defaults[key]['type'] == bool:
            kwargs['action'] = 'store_true'
            del (kwargs['type'])

        if defaults[key]['type'] in [list, tuple]:
            kwargs['type'] = defaults[key]['element_type']
            kwargs['nargs'] = '*'  # '*' - zero or more elements, '+' - one or more elements

        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()

    Delta(**args.__dict__)


def _convert_types(input_dict):
    for key in input_dict.keys():
        for el_key in input_dict[key]:
            if el_key in ['type', 'element_type']:
                input_dict[key][el_key] = eval(input_dict[key][el_key])
    return input_dict


def _read_json(file_name):
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
    except IOError:
        raise Exception('The specified file <{}> not found!'.format(file_name))
    except ValueError:
        raise Exception('Malformed JSON file <{}>!'.format(file_name))
    return data


if __name__ == '__main__':
    henke_console()
