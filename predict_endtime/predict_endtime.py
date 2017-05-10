#!/usr/bin/python

import datetime
import glob
import os

from dateutil import parser


def predict_endtime(time_format='%Y-%m-%d %H:%M:%S'):
    log_dir = '__srwl_logs__'
    if not os.path.isdir(log_dir):
        raise ValueError('{}: log dir not found'.format(log_dir))

    logs = sorted(glob.glob(os.path.join(log_dir, '*.log')))

    last_log = logs[-1]
    print('\nLog file   : {}'.format(last_log))
    with open(last_log) as f:
        content = f.readlines()
        assert len(content) > 1, '{}: content length is too short'.format(len(content))

    start_row = content[0].strip()
    current_row = content[-1].strip()
    print('Start row  : {}'.format(start_row))
    print('Current row: {}\n'.format(current_row))

    start_timestamp = parser.parse(_parse_time(start_row)).timestamp()
    current_timestamp = parser.parse(_parse_time(current_row)).timestamp()

    elapsed_time = current_timestamp - start_timestamp

    current_particle, total_particles = _parse_progress(current_row)

    left_time = elapsed_time * (total_particles / float(current_particle) - 1)

    end_timestamp = current_timestamp + left_time
    end_time = datetime.datetime.fromtimestamp(end_timestamp).strftime(time_format)

    return end_time, elapsed_time, int(left_time)


def _parse_progress(s):
    info_part = s.split(']:')[1].strip().split()
    return int(info_part[1]), int(info_part[4])


def _parse_time(s):
    return s.split(']:')[0].split('[')[1]


if __name__ == '__main__':
    end_time, elapsed_time, left_time = predict_endtime()
    print('Estimated end time       : {}'.format(end_time))
    print('Elapsed/left time (h:m:s): {} / {} '.format(
        str(datetime.timedelta(seconds=elapsed_time)),
        str(datetime.timedelta(seconds=left_time)),
    ))
    print('Total duration (h:m:s)   : {}'.format(
        str(datetime.timedelta(seconds=elapsed_time + left_time)),
    ))