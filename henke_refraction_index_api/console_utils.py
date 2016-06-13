import json
import os


def console(class_name, parameters_file):
    import argparse

    data = read_json(parameters_file)
    description = data['description']
    defaults = convert_types(data['parameters'])

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

    class_name(**args.__dict__)


def convert_types(input_dict):
    for key in input_dict.keys():
        for el_key in input_dict[key]:
            if el_key in ['type', 'element_type']:
                input_dict[key][el_key] = eval(input_dict[key][el_key])
    return input_dict


def defaults_file(defaults_file_path=None, suffix=None):
    script_path = os.path.dirname(os.path.realpath(__file__))

    # Fix for Jython:
    try:
        script_path = script_path.replace(os.path.join(format(os.environ['HOME']), '.jython-cache/cachedir/classes'),
                                          '')
    except:
        pass

    dat_dir = os.path.join(script_path, 'dat')
    config_dir = os.path.join(script_path, 'configs')
    if not defaults_file_path:
        file_name = 'defaults_{}.json'.format(suffix) if suffix else 'defaults.json'
        defaults_file = os.path.join(config_dir, file_name)
    else:
        defaults_file = defaults_file_path

    return {
        'dat_dir': dat_dir,
        'config_dir': config_dir,
        'defaults_file': defaults_file,
    }


def read_json(file_name):
    try:
        with open(file_name, 'r') as f:
            data = json.load(f)
    except IOError:
        raise Exception('The specified file <{}> not found!'.format(file_name))
    except ValueError:
        raise Exception('Malformed JSON file <{}>!'.format(file_name))
    return data
