#!/usr/bin/python

import argparse
import datetime
import glob
import os

import dateutil.parser as dt_parser


def predict_endtime(log_file=None, time_format='%Y-%m-%d %H:%M:%S'):
    log_dir = '__srwl_logs__'
    if not os.path.isdir(log_dir):
        raise ValueError('{}: log dir not found'.format(log_dir))

    if not log_file:
        logs = sorted(glob.glob(os.path.join(log_dir, '*.log')))
        last_log = logs[-1]
    else:
        last_log = log_file

    if not os.path.isfile(last_log):
        raise OSError('{}: file does not exist'.format(last_log))

    print('\nLog file   : {}'.format(last_log))
    with open(last_log) as f:
        content = f.readlines()
        assert len(content) > 1, '{}: content length is too short'.format(len(content))

    start_row = content[0].strip()
    current_row = content[-1].strip()
    print('Start row  : {}'.format(start_row))
    print('Current row: {}\n'.format(current_row))

    start_timestamp = _get_timestamp(start_row)
    current_timestamp = _get_timestamp(current_row)

    elapsed_time = current_timestamp - start_timestamp

    current_particle, total_particles = _parse_progress(current_row)

    left_time = elapsed_time * (total_particles / float(current_particle) - 1)

    end_timestamp = current_timestamp + left_time
    end_time = datetime.datetime.fromtimestamp(end_timestamp).strftime(time_format)

    return end_time, elapsed_time, int(left_time)


def _get_timestamp(s):
    return dt_parser.parse(_parse_time(s)).timestamp()


def _parse_progress(s):
    info_part = s.split(']:')[1].strip().split()
    return int(info_part[1]), int(info_part[4])


def _parse_time(s):
    return s.split(']:')[0].split('[')[1]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Estimate end time of SRW partially-coherent simulations')
    parser.add_argument('-l', '--log-file', dest='log_file', default=None, help='SRW log file to process')
    args = parser.parse_args()

    end_time, elapsed_time, left_time = predict_endtime(args.log_file)
    print('Estimated end time       : {}'.format(end_time))
    print('Elapsed/left time (h:m:s): {} / {} '.format(
        str(datetime.timedelta(seconds=elapsed_time)),
        str(datetime.timedelta(seconds=left_time)),
    ))
    print('Total duration (h:m:s)   : {}'.format(
        str(datetime.timedelta(seconds=elapsed_time + left_time)),
    ))
