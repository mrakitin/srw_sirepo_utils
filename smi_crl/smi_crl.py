# -*- coding: utf-8 -*-

from __future__ import division

import copy
import math

try:
    import numpy as np

    NUMPY = True
except:
    NUMPY = False

NUMPY = False  # explicitly avoid usage of NumPy.
_DL_lens = 2e-3  # distance between two lenses within a cartridge [m].
_DL_cart = 30e-3  # distance between centers of two neighbouring cartridges.
_R_array = [50, 200, 500]  # radii of available lenses in different cartridges [um].
_LENS_array = [1, 2, 4, 8, 16]  # possible number of lenses in cartridges.
_P0 = 6.2  # distance from z=50.9 m to the first lens in the most upstream cartridge at the most upstream position of the transfocator.
_ENERGY = 24000.0  # eV
_TETA0 = 60e-6  # rad

_LENS_CONFIG = {}
for i in _R_array:
    for j in _LENS_array:
        _LENS_CONFIG['T_{}_{}'.format(j, i)] = {
            'radius': i * 1e-6,
            'lens_number': j,
        }

_TRANSFOCATOR_CONFIG = [
    {
        'id': 1,
        'name': 'T_1_500',
        'offset_cart': 2,
    },
    {
        'id': 2,
        'name': 'T_2_50',
        'offset_cart': 3,
    },
    {
        'id': 3,
        'name': 'T_8_500',
        'offset_cart': 4,
    },
    {
        'id': 4,
        'name': 'T_4_50',
        'offset_cart': 5,
    },
    {
        'id': 5,
        'name': 'T_1_200',
        'offset_cart': 6,
    },
    {
        'id': 6,
        'name': 'T_16_50',
        'offset_cart': 7,
    },
    {
        'id': 7,
        'name': 'T_8_50',
        'offset_cart': 9,
    },
    {
        'id': 8,
        'name': 'T_1_50',
        'offset_cart': 11,
    },
]


def calc_ideal_lens(R, N, delta):
    return R / (2 * N * delta)


def calc_lens_array(R, N):
    """Calculate accumulated T_fs for one cartridge with fixed radius.

    :param R: radius.
    :param N: number of lenses in one cartridge.
    :return T_fs_accum: accumulated T_fs.
    """
    T_dl = _calc_T_dl(_DL_lens)
    T_fs = _calc_T_fs(_calc_fs(R, _calc_delta()['delta']))

    T_fs_accum = dot(matrix_power(dot(T_fs, T_dl), N - 1), T_fs)
    return T_fs_accum


def calc_T_total(cart_ids):
    dist_list = []
    for i in range(len(cart_ids) - 1):
        dist_list.append(_calc_distance(cart_ids[i], cart_ids[i + 1]))

    R_list = []
    N_list = []
    for i in range(len(cart_ids)):
        for j in range(len(_TRANSFOCATOR_CONFIG)):
            if cart_ids[i] == _TRANSFOCATOR_CONFIG[j]['id']:
                R_list.append(_LENS_CONFIG[_TRANSFOCATOR_CONFIG[j]['name']]['radius'])
                N_list.append(_LENS_CONFIG[_TRANSFOCATOR_CONFIG[j]['name']]['lens_number'])

    if len(cart_ids) == 1:
        T = calc_lens_array(R_list[0], N_list[0])
    elif len(cart_ids) > 1:
        A = _calc_T_dl(dist_list[0])
        B = calc_lens_array(R_list[0], N_list[0])
        T = dot(A, B)
        for i in range(len(cart_ids) + len(cart_ids) - 3):
            if i % 2 == 0:
                B = calc_lens_array(R_list[int((i + 2) / 2)], N_list[int((i + 2) / 2)])
                T = dot(B, T)
            else:
                A = _calc_T_dl(dist_list[int((i + 1) / 2)])
                T = dot(A, T)
    else:
        raise Exception('No lenses in the beam!')

    return T


def calc_y_teta(T, y0, teta0):
    return dot(T, [y0, teta0])


def dot(A, B, use_numpy=NUMPY):
    """Multiplies matrix A by matrix B."""
    if use_numpy:
        C = np.dot(A, B)
    else:
        B0 = B[0]
        lenB = len(B)
        lenA = len(A)
        if len(A[0]) != lenB:  # Check matrix dimensions
            raise Exception('Matrices have wrong dimensions')
        if isinstance(B0, list) or isinstance(B0, tuple):  # B is matrix
            lenB0 = len(B0)
            C = [[0 for _ in range(lenB0)] for _ in range(lenA)]
            for i in range(lenA):
                for j in range(lenB0):
                    for k in range(lenB):
                        C[i][j] += A[i][k] * B[k][j]
        else:  # B is vector
            C = [0 for _ in range(lenB)]
            for i in range(lenA):
                for k in range(lenB):
                    C[i] += A[i][k] * B[k]
    return C


def matrix_power(A, n, use_numpy=NUMPY):
    """Multiply matrix A n times.

    :param A: input square matrix.
    :param n: power.
    :return B: resulted matrix.
    """
    if use_numpy:
        B = np.linalg.matrix_power(A, n)
    else:
        B = copy.deepcopy(A)
        for i in range(n - 1):
            B = dot(A, B, use_numpy=use_numpy)
    return B


def _calc_delta(energy=_ENERGY, data_file='Be_delta.dat', use_numpy=NUMPY):
    skiprows = 2
    energy_column = 0
    delta_column = 1
    error_msg = 'Error! Use energy range from {} to {} eV.'
    if use_numpy:
        data = np.loadtxt(data_file, skiprows=skiprows)
        try:
            idx_previous = np.where(data[:, energy_column] <= energy)[0][-1]
            idx_next = np.where(data[:, energy_column] > energy)[0][0]
        except IndexError:
            raise Exception(error_msg.format(data[0, energy_column], data[-1, energy_column]))

        idx = idx_previous if abs(data[idx_previous, energy_column] - energy) <= abs(
            data[idx_next, energy_column] - energy) else idx_next
        found_energy = data[idx][energy_column]
        delta = data[idx][delta_column]
    else:
        found_energy = None
        delta = None
        with open(data_file, 'r') as f:
            content = f.readlines()
            energies = []
            deltas = []
            for i in range(skiprows, len(content)):
                energies.append(float(content[i].split()[energy_column]))
                deltas.append(float(content[i].split()[delta_column]))
            indices_previous = []
            indices_next = []
            try:
                for i in range(len(energies)):
                    if energies[i] <= energy:
                        indices_previous.append(i)
                    else:
                        indices_next.append(i)
                idx_previous = indices_previous[-1]
                idx_next = indices_next[0]
            except IndexError:
                raise Exception(error_msg.format(energies[0], energies[-1]))

            idx = idx_previous if abs(energies[idx_previous] - energy) <= abs(energies[idx_next] - energy) else idx_next
            found_energy = energies[idx]
            delta = deltas[idx]
    return {
        'energy': found_energy,
        'delta': delta
    }


def _calc_distance(id1, id2):
    el_num1 = _find_element_by_id(id1)
    el_num2 = _find_element_by_id(id2)
    if not el_num1 or not el_num2:
        raise Exception('Provided id\'s are not valid!')

    coord1 = _TRANSFOCATOR_CONFIG[el_num1]['offset_cart'] * _DL_cart
    lens_num1 = _LENS_CONFIG[_TRANSFOCATOR_CONFIG[el_num1]['name']]['lens_number']
    coord2 = _TRANSFOCATOR_CONFIG[el_num2]['offset_cart'] * _DL_cart

    return coord2 - coord1 - lens_num1 * _DL_lens


def _calc_fs(R, delta):
    return R / (2 * delta)


def _calc_T_dl(dl):
    T_dl = [
        [1, dl],
        [0, 1],
    ]
    return T_dl


def _calc_T_fs(fs):
    T_fs = [
        [1, 0],
        [-1 / fs, 1],
    ]
    return T_fs


def _find_element_by_id(id, data=_TRANSFOCATOR_CONFIG):
    element_number = None
    for i in range(len(data)):
        if id == data[i]['id']:
            element_number = i
            break
    return element_number


if __name__ == '__main__':
    y0 = _P0 * math.tan(_TETA0)
    T = calc_T_total([2, 4, 6])

    v = calc_y_teta(T, y0, _TETA0)

    P1 = v[0] / math.tan(math.pi - v[1])

    f0 = calc_ideal_lens(_LENS_CONFIG['T_1_50']['radius'], 22, _calc_delta()['delta'])
    P1_ideal = (1 / (1 / f0 - 1 / _P0))

    print()
