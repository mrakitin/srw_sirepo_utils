#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Get Index of Refraction from http://henke.lbl.gov/optical_constants/getdb2.html.
Author: Maksim Rakitin (BNL)
2016
"""

import requests

SERVER = 'http://henke.lbl.gov'
CGI_CODE = '/cgi-bin/getdb.pl'
POST_URL = '{}{}'.format(SERVER, CGI_CODE)


def _get_file_name(formula='Be', e_min=30, e_max=30000, n_points=500):
    payload = {
        'Density': -1,
        'Formula': formula,
        'Material': 'Enter Formula',
        'Min': e_min,
        'Max': e_max,
        'Npts': n_points,
        'Output': 'Text File',
        'Scan': 'Energy',
    }
    r = requests.post(POST_URL, payload)
    content = r.text

    # The file name should be something like '/tmp/xray2565.dat':
    try:
        file_name = str(content.split('URL=')[1].split('>')[0].replace('"', ''))
    except:
        raise Exception('\n\nFile name cannot be found! Server response:\n<{}>'.format(content.strip()))

    return file_name


def _get_file_content(file_name):
    get_url = '{}{}'.format(SERVER, file_name)
    r = requests.get(get_url)
    content = r.text

    return content


file_content = _get_file_content(_get_file_name(e_min=30, e_max=30000, n_points=1))

print(file_content)
