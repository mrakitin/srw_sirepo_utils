"""
This script is to parse Sirepo-generated .py file and to produce JSON-file with the parsed data.
It's highly dependent on the external Sirepo/SRW libraries and is written to allow parsing of the .py files using
SRW objects. Can be used in the future for parsing of complicated scripts.
"""

import ast
import json
import os
import pprint
import sys

import requests
from srwl_bl import srwl_uti_std_options

try:
    import cPickle as pickle
except:
    import pickle


def get_json(json_url):
    return json.loads(requests.get(json_url).text)


static_url = 'https://raw.githubusercontent.com/radiasoft/sirepo/master/sirepo/package_data/static'
static_js_url = static_url + '/js'
static_json_url = static_url + '/json'


def list2dict(data_list):
    """
    The function converts list of lists to a dictionary with keys from 1st elements and values from 3rd elements.

    :param data_list: list of SRW parameters (e.g., 'appParam' in Sirepo's *.py files).
    :return out_dict: dictionary with all parameters.
    """

    out_dict = {}

    for i in range(len(data_list)):
        out_dict[data_list[i][0]] = data_list[i][2]

    return out_dict


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


# For sourceIntensityReport:
try:
    import py.path
    from pykern import pkresource

    static_dir = py.path.local(pkresource.filename('static'))
except:
    static_dir = '/home/vagrant/src/radiasoft/sirepo/sirepo/package_data/static'

static_js_dir = static_dir + '/js'
static_json_dir = static_dir + '/json'


def get_default_drift():
    """The function parses srw.js file to find the default values for drift propagation parameters, which can be
    sometimes missed in the exported .py files (when distance = 0), but should be presented in .json files.

    :return default_drift_prop: found list as a string.
    """

    try:
        file_content = requests.get(static_js_url + '/srw.js').text
    except:
        file_content = u''

    default_drift_prop = u'[0, 0, 1, 1, 0, 1.0, 1.0, 1.0, 1.0]'

    try:  # open(file_name, 'r') as f:
        content = file_content.split('\n')
        for i in range(len(content)):
            if content[i].find('function defaultDriftPropagationParams()') >= 0:
                # Find 'return' statement:
                for j in range(10):
                    '''
                        function defaultDriftPropagationParams() {
                            return [0, 0, 1, 1, 0, 1.0, 1.0, 1.0, 1.0];
                        }
                    '''
                    if content[i + j].find('return') >= 0:
                        default_drift_prop = content[i + j].replace('return ', '').replace(';', '').strip()
                        break
                break
    except:
        pass

    default_drift_prop = ast.literal_eval(default_drift_prop)

    return default_drift_prop


# Mapping all the values to a dictionary:
def beamline_element(obj, idx, title, elem_type, position):
    data = {}

    data['id'] = idx
    data['type'] = unicode(elem_type)
    data['title'] = unicode(title)  # u'S0',
    data['position'] = position  # 20.5

    if elem_type == 'aperture':
        data['shape'] = unicode(obj.shape)  # u'r'

        data['horizontalOffset'] = obj.x  # 0
        data['verticalOffset'] = obj.y  # 0,
        data['horizontalSize'] = obj.Dx * 1e3  # 0.2
        data['verticalSize'] = obj.Dy * 1e3  # 1

    elif elem_type == 'mirror':
        keys = ['grazingAngle', 'heightAmplification', 'heightProfileFile', 'horizontalTransverseSize',
                'orientation', 'verticalTransverseSize']
        for key in keys:
            data[key] = obj.input_parms[0][key]

        # Should be multiplied by 1000.0:
        for key in ['horizontalTransverseSize', 'verticalTransverseSize']:
            data[key] *= 1000.0

        data['heightProfileFile'] = 'mirror_1d.dat'

    elif elem_type == 'crl':
        keys = ['attenuationLength', 'focalPlane', 'horizontalApertureSize', 'numberOfLenses', 'radius',
                'refractiveIndex', 'shape', 'verticalApertureSize', 'wallThickness']

        for key in keys:
            data[key] = obj.input_parms[key]

        # Should be multiplied by 1000.0:
        for key in ['horizontalApertureSize', 'verticalApertureSize']:
            data[key] *= 1000.0

        '''
        data['attenuationLength'] = None  # u'7.31294e-03'
        if obj.Fx > 1e20 and obj.Fy < 1e20:
            data['focalPlane'] = 2  # 2
        else:
            data['focalPlane'] = 1
        data['horizontalApertureSize'] = None  # u'1'
        data['numberOfLenses'] = None  # u'1'
        data['radius'] = None  # u'1.5e-03'
        data['refractiveIndex'] = None  # u'4.20756805e-06'
        data['shape'] = None  # 1
        data['verticalApertureSize'] = None  # u'2.4'
        data['wallThickness'] = None  # u'80.e-06'
        '''

    elif elem_type == 'lens':
        data['horizontalFocalLength'] = obj.Fx  # u'3.24479',
        data['horizontalOffset'] = obj.x  # 0
        data['verticalFocalLength'] = obj.Fy  # u'1.e+23'
        data['verticalOffset'] = obj.y  # 0

    else:
        pass

    return data


def get_beamline(obj_arOpt, init_distance=20.0):
    """The function creates a beamline from the provided object and/or AST tree.

    :param obj_arOpt: SRW object containing properties of the beamline elements.
    :param init_distance: distance from the source to the first element (20.0 m by default).
    :return elements_list: list of all found beamline elements.
    """

    num_elements = len(obj_arOpt)

    elements_list = []

    # The dictionary to count the elements of different types:
    names = {
        'S': 0,
        'O': '',
        'HDM': 0,
        'CRL': 0,
        'KL': '',
        'KLA': '',
        'Sample': '',
    }

    positions = []  # a list with sequence of distances between elements
    positions_from_source = []  # a list with sequence of distances from source

    for i in range(num_elements):
        name = obj_arOpt[i].__class__.__name__
        try:
            next_name = obj_arOpt[i + 1].__class__.__name__
        except:
            next_name = None

        if name != 'SRWLOptD':  # or i == len(obj_arOpt) - 1:  # not drift
            # Check if the next element is drift, else put 0 distance:
            if next_name == 'SRWLOptD':
                positions.append(obj_arOpt[i + 1].L)
            else:
                positions.append(0.0)

    positions_from_source.append(init_distance)  # add distance to the first element
    for i in range(len(positions)):
        dist_from_source = init_distance + sum(positions[:i + 1])
        positions_from_source.append(str(dist_from_source))

    counter = 0

    for i in range(num_elements):
        name = obj_arOpt[i].__class__.__name__
        if name != 'SRWLOptD' or i == len(obj_arOpt) - 1:  # drifts are not included in the list, except the last drift
            counter += 1

            data = []
            title = ''
            elem_type = ''

            if name == 'SRWLOptA':
                if obj_arOpt[i].ap_or_ob == 'a':
                    elem_type = 'aperture'
                    key = 'S'
                else:
                    elem_type = 'obstacle'
                    key = 'O'

                names[key] += 1

            elif name == 'SRWLOptT':
                # Check the type based on focal lengths of the element:
                if type(obj_arOpt[i].input_parms) == tuple:
                    elem_type = obj_arOpt[i].input_parms[0]['type']
                else:
                    elem_type = obj_arOpt[i].input_parms['type']

                if elem_type == 'mirror':  # mirror, no surface curvature
                    key = 'HDM'

                elif elem_type == 'crl':  # CRL
                    key = 'CRL'

                names[key] += 1

            elif name == 'SRWLOptL':
                key = 'KL'
                elem_type = 'lens'

            if i == len(obj_arOpt) - 1:
                key = 'Sample'
                elem_type = 'watch'

            title = key + str(names[key])

            data = beamline_element(obj_arOpt[i], counter, title, elem_type, positions_from_source[counter - 1])

            elements_list.append(data)

    return elements_list


def get_propagation(op):
    prop_dict = {}
    counter = 0
    for i in range(len(op.arProp) - 1):
        name = op.arOpt[i].__class__.__name__
        try:
            next_name = op.arOpt[i + 1].__class__.__name__
        except:
            next_name = None
        if name != 'SRWLOptD' or i == len(op.arProp) - 2:  # drifts are not included in the list, except the last drift
            counter += 1
            prop_dict[unicode(str(counter))] = [op.arProp[i]]
            if next_name == 'SRWLOptD':
                prop_dict[unicode(str(counter))].append(op.arProp[i + 1])
            else:
                prop_dict[unicode(str(counter))].append(get_default_drift())

    return prop_dict


def parsed_dict(v, op):
    std_options = Struct(**list2dict(srwl_uti_std_options()))

    beamlines_list = get_beamline(op.arOpt, v.op_r)

    def _default_value(parm, obj, std, def_val=None):
        if not hasattr(obj, parm):
            try:
                return getattr(std, parm)
            except:
                if def_val is not None:
                    return def_val
                else:
                    return ''
        try:
            return getattr(obj, parm)
        except:
            if def_val is not None:
                return def_val
            else:
                return ''

    try:
        idx = beamlines_list[-1]['id']
    except:
        idx = ''

    # Format the key name to be consistent with Sirepo:
    watchpointReport_name = u'watchpointReport{}'.format(idx)

    # This dictionary will is used for both initial intensity report and for watch point:
    initialIntensityReport = {
        u'characteristic': v.si_type,  # 0,
        u'horizontalPosition': v.w_x,  # 0,
        u'horizontalRange': v.w_rx * 1e3,  # u'0.4',
        u'polarization': v.si_pol,  # 6,
        u'precision': v.w_prec,  # Static values in .py template: 0.01,
        u'verticalPosition': v.w_y,  # 0,
        u'verticalRange': v.w_ry * 1e3,  # u'0.6',
    }

    python_dict = {
        u'models': {
            u'beamline': beamlines_list,  # get_beamline(op.arOpt, v.op_r),
            u'electronBeam': {
                u'beamSelector': unicode(v.ebm_nm),  # u'NSLS-II Low Beta Day 1',
                u'current': v.ebm_i,  # 0.5,
                u'energy': _default_value('ueb_e', v, std_options, 3.0),  # None,  # app.ueb_e,  # 3,
                u'energyDeviation': _default_value('ebm_de', v, std_options, 0.0),  # v.ebm_de,  # 0,
                u'horizontalAlpha': _default_value('ueb_alpha_x', v, std_options, 0.0),
                # None,  # app.ueb_alpha_x,  # 0,
                u'horizontalBeta': _default_value('ueb_beta_x', v, std_options, 2.02),
                # None,  # app.ueb_beta_x,  # 2.02,
                u'horizontalDispersion': _default_value('ueb_eta_x', v, std_options, 0.0),
                # None,  # app.ueb_eta_x,  # 0,
                u'horizontalDispersionDerivative': _default_value('ueb_eta_x_pr', v, std_options, 0.0),
                # None,  # app.ueb_eta_x_pr,  # 0,
                u'horizontalEmittance': _default_value('ueb_emit_x', v, std_options, 9e-10) * 1e9,
                # None,  # app.ueb_emit_x * 1e9,  # 0.9,
                u'horizontalPosition': v.ebm_x,  # 0,
                u'isReadOnly': False,
                u'name': unicode(v.ebm_nm),  # u'NSLS-II Low Beta Day 1',
                u'rmsSpread': _default_value('ueb_sig_e', v, std_options, 0.00089),
                # None,  # app.ueb_sig_e,  # 0.00089,
                u'verticalAlpha': _default_value('ueb_alpha_y', v, std_options, 0.0),  # None,  # app.ueb_alpha_y,  # 0,
                u'verticalBeta': _default_value('ueb_beta_y', v, std_options, 1.06),
                # None,  # app.ueb_beta_y,  # 1.06,
                u'verticalDispersion': _default_value('ueb_eta_y', v, std_options, 0.0),
                # None,  # app.ueb_eta_y,  # 0,
                u'verticalDispersionDerivative': _default_value('ueb_eta_y_pr', v, std_options, 0.0),
                # None,  # app.ueb_eta_y_pr,  # 0,
                u'verticalEmittance': _default_value('ueb_emit_y', v, std_options, 8e-12) * 1e9,
                # None,  # app.ueb_emit_y * 1e9,  # 0.008,
                u'verticalPosition': v.ebm_y,  # 0
            },
            u'electronBeams': [],
            u'fluxReport': {
                u'azimuthalPrecision': v.sm_pra,  # 1,
                u'distanceFromSource': v.op_r,  # 20.5,
                u'finalEnergy': v.sm_ef,  # 20000,
                u'fluxType': v.sm_type,  # 1,
                u'horizontalApertureSize': v.sm_rx * 1e3,  # u'1',
                u'horizontalPosition': v.sm_x,  # 0,
                u'initialEnergy': v.sm_ei,  # u'100',
                u'longitudinalPrecision': v.sm_prl,  # 1,
                u'photonEnergyPointCount': v.sm_ne,  # 10000,
                u'polarization': v.sm_pol,  # 6,
                u'verticalApertureSize': v.sm_ry * 1e3,  # u'1',
                u'verticalPosition': v.sm_y,  # 0,
            },
            u'initialIntensityReport': {
                u'characteristic': v.si_type,  # 0,
                u'horizontalPosition': v.w_x,  # 0,
                u'horizontalRange': v.w_rx * 1e3,  # u'0.4',
                u'polarization': v.si_pol,  # 6,
                u'precision': v.w_prec,  # Static values in .py template: 0.01,
                u'verticalPosition': v.w_y,  # 0,
                u'verticalRange': v.w_ry * 1e3,  # u'0.6',
            },
            u'intensityReport': {
                u'distanceFromSource': v.op_r,  # 20.5,
                u'finalEnergy': v.ss_ef,  # u'20000',
                u'horizontalPosition': v.ss_x,  # u'0',
                u'initialEnergy': v.ss_ei,  # u'100',
                u'photonEnergyPointCount': v.ss_ne,  # 10000,
                u'polarization': v.ss_pol,  # 6,
                u'precision': v.ss_prec,  # 0.01,
                u'verticalPosition': v.ss_y,  # 0,
            },
            u'postPropagation': op.arProp[-1],  # [0, 0, u'1', 0, 0, u'0.3', u'2', u'0.5', u'1'],
            u'powerDensityReport': {
                u'distanceFromSource': v.op_r,  # 20.5,
                u'horizontalPointCount': v.pw_nx,  # 100,
                u'horizontalPosition': v.pw_x,  # u'0',
                u'horizontalRange': v.pw_rx * 1e3,  # u'15',
                u'method': v.pw_meth,  # 1,
                u'precision': v.pw_pr,  # u'1',
                u'verticalPointCount': v.pw_ny,  # 100,
                u'verticalPosition': v.pw_y,  # u'0',
                u'verticalRange': v.pw_ry * 1e3,  # u'15',
            },
            u'propagation': get_propagation(op),
            u'simulation': {
                u'facility': unicode(v.ebm_nm.split()[0]),  # unicode(v.name.split()[0]),  # u'NSLS-II',
                u'horizontalPointCount': v.w_nx,  # 100,
                u'isExample': 0,  # u'1',
                u'name': unicode(v.ebm_nm),  # unicode(v.name),  # u'NSLS-II CHX beamline',
                u'photonEnergy': v.w_e,  # u'9000',
                u'sampleFactor': v.w_smpf,  # 1,
                u'simulationId': '',  # None,  # u'1YA8lSnj',
                u'sourceType': u'u',
                # unicode(_default_value('source_type', v, std_options)),  # app.source_type,  # u'u',
                u'verticalPointCount': v.w_ny,  # 100
            },
            u'sourceIntensityReport': get_json(static_json_url + '/srw-default.json')['models'][
                'sourceIntensityReport'],
            u'undulator': {
                u'horizontalAmplitude': _default_value('und_bx', v, std_options, 0.0),  # v.und_bx,  # u'0',
                u'horizontalInitialPhase': _default_value('und_phx', v, std_options, 0.0),  # v.und_phx,  # 0,
                u'horizontalSymmetry': v.und_sx,  # 1,
                u'length': v.und_len,  # u'3',
                u'longitudinalPosition': v.und_zc,  # 0,
                u'period': v.und_per * 1e3,  # u'20',
                u'verticalAmplitude': _default_value('und_by', v, std_options, 0.88770981),
                # v.und_by,  # u'0.88770981',
                u'verticalInitialPhase': _default_value('und_phy', v, std_options, 0.0),  # v.und_phy,  # 0,
                u'verticalSymmetry': v.und_sy,  # -1
            },
            watchpointReport_name: initialIntensityReport,
            u'gaussianBeam': {
                u'energyPerPulse': 0,
                # _default_value('gbm_pen', v, std_options),  # app.gb_energy_per_pulse,  # u'0.001',
                u'polarization': 1,  # _default_value('gbm_pol', v, std_options),  # app.gb_polarization,  # 1,
                u'rmsPulseDuration': 0,  # _default_value('gbm_st', v, std_options),
                # app.gb_rms_pulse_duration * 1e12,  # 0.1,
                u'rmsSizeX': 0,  # _default_value('gbm_sx', v, std_options),  # app.gb_rms_size_x * 1e6,  # u'9.78723',
                u'rmsSizeY': 0,  # _default_value('gbm_sy', v, std_options),  # app.gb_rms_size_y * 1e6,  # u'9.78723',
                u'waistAngleX': 0,  # _default_value('gbm_xp', v, std_options),  # app.gb_waist_angle_x,  # 0,
                u'waistAngleY': 0,  # _default_value('gbm_yp', v, std_options),  # app.gb_waist_angle_y,  # 0,
                u'waistX': 0,  # _default_value('gbm_x', v, std_options),  # app.gb_waist_x,  # 0,
                u'waistY': 0,  # _default_value('gbm_y', v, std_options),  # app.gb_waist_y,  # 0,
                u'waistZ': 0,  # _default_value('gbm_z', v, std_options),  # app.gb_waist_z,  # 0,
            },
            u'multipole': {
                u'distribution': "n",  # _default_value('mp_distribution', v, std_options),
                # unicode(app.mp_distribution),  # u'n',
                u'field': 0,  # _default_value('mp_field', v, std_options),  # app.mp_field,  # 0.4,
                u'length': 0,  # _default_value('mp_len', v, std_options),  # app.mp_len,  # 3,
                u'order': 1,  # _default_value('mp_order', v, std_options),  # app.mp_order,  # 1,
            },
        },
        u'report': u'',  # u'powerDensityReport',
        u'simulationType': u'srw',
        u'version': unicode(get_json(static_json_url + '/schema-common.json')['version']),  # u'20160120',
    }

    return python_dict


class SRWParser:
    def __init__(self, data, isFile=True, save_vars=False, save_file='parsed_sirepo.json', clean=True):
        self.content = None
        self.isFile = isFile
        if self.isFile:
            self.infile = data
        else:
            self.content = data
            self.infile = 'imported_srw_file.py'
            with open(self.infile, 'w') as f:
                f.write(self.content)

        # If it's set to True, save variables in *.pickle files:
        self.save_vars = save_vars

        # The resulted JSON contents will be saved in this file:
        self.save_file = save_file

        # If we need to clean used *.py/*.pyc files:
        self.clean = clean

        # Module name is used for __import__:
        self.module_name = os.path.splitext(os.path.basename(self.infile))[0]

        # Important objects from the parsed file:
        self.v = None  # object containing parameters from varParam list
        self.op = None  # object containing propagation parameters and beamline elements

        # Reference to access imported values:
        self.imported_srw_file = None

        # List of mirror and other *.dat and *.pickle files:
        self.list_of_files = []

        # Directory name to store the uploaded *.dat/*.pickle files:
        self.fdir = ''

        # JSON content for Sirepo:
        self.json_content = None

        # Define the names of the function and the list to read:
        self.set_optics_func = 'set_optics'
        self.varParam_parm = 'varParam'

        # Perform import, read 'v' variable and get *.dat/*.pickle files on creation of the object:
        self.perform_import()
        self.read_v()
        self.get_files()

    def perform_import(self):
        sys.path.append(os.path.abspath(os.getcwd()))
        self.imported_srw_file = __import__(self.module_name, fromlist=[self.set_optics_func, self.varParam_parm])
        # Remove temporary .py and .pyc files, we don't need them anymore:
        if self.clean:
            for f in [self.infile, self.infile + 'c']:
                try:
                    os.remove(f)
                except:
                    pass

    def read_v(self):
        varParam = getattr(self.imported_srw_file, self.varParam_parm)
        self.v = Struct(**list2dict(varParam))

    def get_files(self):
        for key in self.v.__dict__.keys():
            if key.find('_ifn') >= 0:
                self.list_of_files.append(self.v.__dict__[key])
            if key.find('fdir') >= 0:
                self.fdir = self.v.__dict__[key]

    # Since it's a long procedure, it's done separately:
    def read_op(self):
        set_optics = getattr(self.imported_srw_file, self.set_optics_func)
        self.op = set_optics(self.v)

    def to_json(self):
        if self.save_vars:
            pickle_file_v = 'pickle_v.txt'
            pickle_file_op = 'pickle_op.txt'

            if not os.path.isfile(pickle_file_v) or not os.path.isfile(pickle_file_op):
                self.read_op()

                with open(pickle_file_v, 'w') as f:
                    pickle.dump(self.v, f)
                with open(pickle_file_op, 'w') as f:
                    pickle.dump(self.op, f)
            else:
                with open(pickle_file_v, 'r') as f:
                    self.v = pickle.load(f)
                with open(pickle_file_op, 'r') as f:
                    self.op = pickle.load(f)
        else:
            self.read_op()

        self.json_content = parsed_dict(self.v, self.op)

    def save(self):
        with open(self.save_file, 'w') as f:
            json.dump(
                self.json_content,
                f,
                sort_keys=True,
                indent=4,
                separators=(',', ': '),
            )


def main(py_file, debug=False):
    o = SRWParser(py_file, clean=False)
    # Here we may process .dat files:
    # ...
    print 'List of .dat files:', o.list_of_files

    # Main SRW calculation and conversion to JSON:
    o.to_json()

    # Save the resulted file:
    o.save()

    if debug:
        pprint.pprint(o.json_content)
        print '\n\tJSON output is saved in <%s>.' % o.save_file

    return


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Parse Sirepo-generated .py file.')
    parser.add_argument('-p', '--py_file', dest='py_file', help='input Python file.')
    parser.add_argument('-d', '--debug', action='store_true', dest='debug', help='enable debug information.')

    args = parser.parse_args()
    py_file = args.py_file
    debug = args.debug

    if py_file and os.path.isfile(py_file):
        sys.exit(main(py_file, debug))
