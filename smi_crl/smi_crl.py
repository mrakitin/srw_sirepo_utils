from __future__ import division

import numpy as np

_DL_lens = 2e-3  # distance between two lenses within a cartridge [m].
_DL_cart = 30e-3  # distance between centers of two neighbouring cartridges.
_R_array = np.array([50, 200, 500]) * 1e-6  # radii of available lenses in different cartridges [m].
_P0 = 6.2  # distance from z=50.9 m to the first lens in the most upstream cartridge at the most upstream position of the transfocator.
_ENERGY = 24000.0  # eV
_LENS_CONFIG = {
    'T_1_50': {
        'radius': 50e-6,
        'lens_number': 1,
    },
    'T_2_50': {
        'radius': 50e-6,
        'lens_number': 2,
    },
    'T_4_50': {
        'radius': 50e-6,
        'lens_number': 4,
    },
    'T_8_50': {
        'radius': 50e-6,
        'lens_number': 8,
    },
    'T_16_50': {
        'radius': 50e-6,
        'lens_number': 16,
    },
    'T_1_200': {
        'radius': 200e-6,
        'lens_number': 1,
    },
    'T_2_200': {
        'radius': 200e-6,
        'lens_number': 2,
    },
    'T_4_200': {
        'radius': 200e-6,
        'lens_number': 4,
    },
    'T_8_200': {
        'radius': 200e-6,
        'lens_number': 8,
    },
    'T_16_200': {
        'radius': 200e-6,
        'lens_number': 16,
    },
    'T_1_500': {
        'radius': 500e-6,
        'lens_number': 1,
    },
    'T_2_500': {
        'radius': 500e-6,
        'lens_number': 2,
    },
    'T_4_500': {
        'radius': 500e-6,
        'lens_number': 4,
    },
    'T_8_500': {
        'radius': 500e-6,
        'lens_number': 8,
    },
    'T_16_500': {
        'radius': 500e-6,
        'lens_number': 16,
    }
}
_TRANSFOCATOR_CONFIG = [
    {
        'id': 1,
        'name': 'T_1_500',
        'distance': 2 * _DL_cart,
        'coordinate': 2 * _DL_cart,
    },
    {
        'id': 2,
        'name': 'T_2_50',
        'distance': _DL_cart - 1 * _DL_lens,
        'coordinate': 3 * _DL_cart,
    },
    {
        'id': 3,
        'name': 'T_8_500',
        'distance': _DL_cart - 2 * _DL_lens,
        'coordinate': 4 * _DL_cart,
    },
    {
        'id': 4,
        'name': 'T_4_50',
        'distance': _DL_cart - 8 * _DL_lens,
        'coordinate': 5 * _DL_cart,
    },
    {
        'id': 5,
        'name': 'T_1_200',
        'distance': _DL_cart - 4 * _DL_lens,
        'coordinate': 6 * _DL_cart,
    },
    {
        'id': 6,
        'name': 'T_16_50',
        'distance': _DL_cart - 1 * _DL_lens,
        'coordinate': 7 * _DL_cart,
    },
    {
        'id': 7,
        'name': 'T_8_50',
        'distance': 2 * _DL_cart - 16 * _DL_lens,
        'coordinate': 9 * _DL_cart,
    },
    {
        'id': 8,
        'name': 'T_1_50',
        'distance': 2 * _DL_cart - 8 * _DL_lens,
        'coordinate': 11 * _DL_cart,
    },
]


def calc_distance(id1, id2):
    for i in range(len(_TRANSFOCATOR_CONFIG)):
        if id1 == _TRANSFOCATOR_CONFIG[i]['id']:
            coord1 = _TRANSFOCATOR_CONFIG[i]['coordinate']
            lens_number1 = _LENS_CONFIG[_TRANSFOCATOR_CONFIG[i]['name']]['lens_number']
        if id2 == _TRANSFOCATOR_CONFIG[i]['id']:
            coord2 = _TRANSFOCATOR_CONFIG[i]['coordinate']
    return coord2 - coord1 - lens_number1 * _DL_lens


def calc_delta(energy=_ENERGY, data_file='Be_delta.dat'):
    data = np.loadtxt(data_file, skiprows=2)
    try:
        idx_next = np.where(data[:, 0] >= energy)[0][0]
        idx_previous = np.where(data[:, 0] <= energy)[0][-1]
    except IndexError:
        raise Exception('Error! Use energy range from {} to {} eV.'.format(data[0, 0], data[-1, 0]))

    if abs(data[idx_previous, 0] - energy) <= abs(data[idx_next, 0] - energy):
        idx = idx_previous
    else:
        idx = idx_next
    return {
        'energy': data[idx, 0],
        'delta': data[idx, 1]
    }


def calc_fs(R, delta):
    return R / (2 * delta)


def calc_T_dl(dl):
    T_dl = np.array([
        [1, dl],
        [0, 1],
    ])
    return T_dl


def calc_T_fs(fs):
    T_fs = np.array([
        [1, 0],
        [-1 / fs, 1],
    ])
    return T_fs


def calc_lens_array(R, N):
    """Calculate accumulated T_fs for one cartridge with fixed radius.

    :param R: radius.
    :param N: number of lenses in one cartridge.
    :return T_fs_accum: accumulated T_fs.
    """
    T_dl = calc_T_dl(_DL_lens)
    T_fs = calc_T_fs(calc_fs(R, calc_delta()['delta']))

    T_fs_accum = np.dot(np.linalg.matrix_power(np.dot(T_fs, T_dl), N - 1), T_fs)
    return T_fs_accum


def calc_T_total(cart_ids):
    dist_list = []
    for i in range(len(cart_ids) - 1):
        dist_list.append(calc_distance(cart_ids[i], cart_ids[i + 1]))

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
        A = calc_T_dl(dist_list[0])
        B = calc_lens_array(R_list[0], N_list[0])
        T = np.dot(A, B)
        for i in range(len(cart_ids) + len(cart_ids) - 3):
            if i % 2 == 0:
                B = calc_lens_array(R_list[int((i + 2) / 2)], N_list[int((i + 2) / 2)])
                T = np.dot(B, T)
            else:
                A = calc_T_dl(dist_list[int((i + 1) / 2)])
                T = np.dot(A, T)
    else:
        raise Exception('No lenses in the beam!')

    return T


def calc_y_teta(T, y0, teta0):
    return np.dot(T, np.array([y0, teta0]))


def calc_ideal_lens(R, N, delta):
    return R / (2 * N * delta)


if __name__ == '__main__':
    teta0 = 60e-6  # rad
    y0 = _P0 * np.tan(teta0)
    T = calc_T_total([2, 4, 6, 7, 8])

    v = calc_y_teta(T, y0, teta0)

    P1 = v[0] / np.tan(np.pi - v[1])

    f0 = calc_ideal_lens(_LENS_CONFIG['T_1_50']['radius'], 31, calc_delta()['delta'])
    P1_ideal = (1 / (1 / f0 - 1 / _P0))

    print()
