#!/usr/bin/python

import datetime
import glob
import os

from dateutil import parser


def predict_endtime(time_format='%Y-%m-%d %H:%M:%S'):
    # parser = argparse.ArgumentParser(description='Estimate/predict endtime of an SRW partially-coherent simulation')
    # parser.add_argument('-l', '--log-file', dest='log_file', default=None, choices=('chx', 'CHX', 'smi', 'SMI'),
    #                     help='select beamline to get data from')

    log_dir = '__srwl_logs__'
    if not os.path.isdir(log_dir):
        raise ValueError('{}: log dir not found'.format(log_dir))

    logs = sorted(glob.glob(os.path.join(log_dir, '*.log')))

    last_log = logs[-1]
    with open(last_log) as f:
        content = f.readlines()
        assert len(content) > 1, '{}: content length is too short'.format(len(content))

    start_row = content[0]
    end_row = content[-1]

    start_timestamp = parser.parse(_parse_time(start_row)).timestamp()
    end_timestamp = parser.parse(_parse_time(end_row)).timestamp()

    elapsed_time = end_timestamp - start_timestamp

    current_particle, total_particles = _parse_progress(end_row)
    left_particles_ratio = float(total_particles - current_particle) / float(total_particles)

    left_seconds = elapsed_time * total_particles / float(current_particle)

    total_timestamp = end_timestamp + left_seconds
    end_time = datetime.datetime.fromtimestamp(total_timestamp).strftime(time_format)

    return end_time


def _parse_progress(s):
    info_part = s.split(']:')[1].strip().split()
    return int(info_part[1]), int(info_part[4])


def _parse_time(s):
    return s.split(']:')[0].split('[')[1]


if __name__ == '__main__':
    end_time = predict_endtime()
    print('Estimated end time: {}'.format(end_time))
