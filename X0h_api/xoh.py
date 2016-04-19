#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Get polarizability from X0h server (http://x-server.gmca.aps.anl.gov/x0h.html).
For details see http://x-server.gmca.aps.anl.gov/pub/Stepanov_CR_1991_08.pdf.
"""

import requests


def _parse_xr_xi(string):
    return float(string.split('=')[-1].strip())


def get_server_data(energy, material, h, k, l):
    """
    The function gets data from the server and splits it by lines.

    :param energy: energy [keV].
    :param material: material, e.g. Silicon or Germanium
    :param h: Miller's index h.
    :param k: Miller's index k.
    :param l: Miller's index l.
    :return content: split server's response.
    """

    url = 'http://x-server.gmca.aps.anl.gov/cgi/X0h_form.exe'
    payload = {
        'xway': 2,
        'wave': energy,
        'coway': 0,
        'code': material,
        'i1': h,
        'i2': k,
        'i3': l,
        'df1df2': -1,
        'modeout': 1,
    }
    r = requests.get(url, params=payload)
    content = r.text
    content = content.split('\n')

    return content


def get_crystal_parameters(content, hr=None):
    """
    Get reflecting planes distance and polarizability from the server's response.

    :param content: split content of the server's response.
    :return d: reflecting planes distance.
    :return xr0, xi0, xrh, xih: polarizability components.
    """

    d = []
    xr0_list = []
    xi0_list = []
    xrh_list = []
    xih_list = []

    for i in range(len(content)):
        if content[i].find('a1=') >= 0:
            d.append(content[i])
        elif content[i].find('xr0') >= 0:
            xr0_list.append(content[i])
        elif content[i].find('xi0') >= 0:
            xi0_list.append(content[i])
        elif content[i].find('xrh') >= 0:
            xrh_list.append(content[i])
        elif content[i].find('xih') >= 0:
            xih_list.append(content[i])

    d = _parse_xr_xi(d[0])
    if hr:
        d /= (sum(n ** 2 for n in hr)) ** 0.5

    xr0 = _parse_xr_xi(xr0_list[0])
    xi0 = _parse_xr_xi(xi0_list[0])
    xrh = _parse_xr_xi(xrh_list[0])
    xih = _parse_xr_xi(xih_list[0])

    return d, xr0, xi0, xrh, xih


if __name__ == '__main__':
    energy = 9  # keV
    h = 1
    k = 1
    l = 1
    for material in ['Silicon', 'Germanium', 'Diamond']:
        content = get_server_data(energy, material, h, k, l)
        d, xr0, xi0, xrh, xih = get_crystal_parameters(content, [h, k, l])
        print('Material: {} (d={} A)\nxr0: {}  xi0: {}\nxrh: {}  xih: {}\n'.format(material, d, xr0, xi0, xrh, xih))
