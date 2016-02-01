"""
This script is to parse Sirepo-generated .py file and to produce JSON-file with the parsed data.
It's highly dependent on the external Sirepo/SRW libraries and is written to allow parsing of the .py files using
SRW objects. Can be used in the future for parsing of complicated scripts.
"""

import os
import json
import pprint
import ast

try:
    import cPickle as pickle
except:
    import pickle

import srwl_bl
from exported_sirepo import get_beamline_optics, get_srw_params, setup_source, appParam

from sirepo.template.srw import run_all_text

pickle_file_v = 'pickle_v.txt'
pickle_file_op = 'pickle_op.txt'

# TODO: This construction is for testing/development purposes. Need to remove it later after the code is implemented.
if not os.path.isfile(pickle_file_v) or not os.path.isfile(pickle_file_op):
    run_function_list = run_all_text().split('\n')

    # Remove empty lines:
    run_function_list = [x for x in run_function_list if x.strip() != '']

    remove_lines = ['if __name__', 'run_all_', 'srwl_bl.']  # template for the lines to remove
    del_rows = []  # full rows contents to remove after the loop
    for i in range(len(run_function_list)):
        for l in remove_lines:
            if run_function_list[i].strip().replace('#', '').strip().find(l) == 0:
                del_rows.append(run_function_list[i])

    # Remove collected rows:
    for i in del_rows:
        run_function_list.remove(i)

    # Add return values for further parsing:
    run_function_list.append('    return v, op')

    run_function = '\n'.join(run_function_list)

    # replace('\ndef', 'def').replace('srwl_bl.SRWLBeamline', '\n    return v, op  # ')

    exec run_function

    v, op = run_all_reports()

    with open(pickle_file_v, 'w') as f:
        pickle.dump(v, f)
    with open(pickle_file_op, 'w') as f:
        pickle.dump(op, f)

else:
    with open(pickle_file_v, 'r') as f:
        v = pickle.load(f)
    with open(pickle_file_op, 'r') as f:
        op = pickle.load(f)


# -----------------------------------------------------------------------------
# Convert appParam to an object:
def app_processing(app_list):
    """
    The function converts list of lists to a dictionary with keys from 1st elements and values from 3rd elements.

    :param app_list: list of user-defined parameters ('appParam' in Sirepo's *.py files).
    :return out_dict: dictionary with all parameters.
    """

    out_dict = {}

    for i in range(len(app_list)):
        out_dict[app_list[i][0]] = app_list[i][2]

    return out_dict


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


args = app_processing(appParam)
app = Struct(**args)

# For sourceIntensityReport:
try:
    import py.path
    from pykern import pkresource

    static_dir = py.path.local(pkresource.filename('static'))
except:
    static_dir = '/home/vagrant/src/radiasoft/sirepo/sirepo/package_data/static'

static_js_dir = static_dir + '/js'
static_json_dir = static_dir + '/json'


def parse_js(file_name):
    """The function parses srw.js file to find the default values for drift propagation parameters, which can be
    sometimes missed in the exported .py files (when distance = 0), but should be presented in .json files.

    :param file_name: full path to srw.js file.
    :return default_drift_prop: found list as a string.
    """

    default_drift_prop = None

    with open(file_name, 'r') as f:
        content = f.readlines()
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

    return default_drift_prop


try:
    default_drift_prop = ast.literal_eval(parse_js(static_js_dir + '/srw.js'))
except:
    default_drift_prop = [0, 0, 1, 1, 0, 1.0, 1.0, 1.0, 1.0]

srw_default_json = static_json_dir + '/srw-default.json'
schema_common_json = static_json_dir + '/schema-common.json'
with open(srw_default_json, 'r') as f:
    srw_default = json.load(f)
with open(schema_common_json, 'r') as f:
    schema_common = json.load(f)


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
        data['grazingAngle'] = None  # u'3.1415926',
        data['heightAmplification'] = None  # u'1',
        data['heightProfileFile'] = None  # u'mirror_1d.dat',
        data['horizontalTransverseSize'] = None  # u'0.94',
        data['orientation'] = None  # u'x'
        data['verticalTransverseSize'] = None  # u'1'

    elif elem_type == 'crl':
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

    elif elem_type == 'lens':
        data['horizontalFocalLength'] = obj.Fx  # u'3.24479',
        data['horizontalOffset'] = obj.x  # 0
        data['verticalFocalLength'] = obj.Fy  # u'1.e+23'
        data['verticalOffset'] = obj.y  # 0

    else:
        pass

    return data


def beamline(obj_arOpt, init_distance=20.0):
    """The function creates a beamline from the provided object and/or AST tree.

    :param obj_arOpt: SRW object containing properties of the beamline elements.
    :param init_distance: distance from the source to the first element (20.0 m by default).
    :return elements_list: list of all found beamline elements.
    """

    num_elements = len(obj_arOpt)

    elements_list = []

    # The dictionary to count the elements of different types:
    names = {
        'S': -1,
        'HDM': '',
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
        positions_from_source.append(dist_from_source)

    counter = 0

    for i in range(num_elements):
        name = obj_arOpt[i].__class__.__name__
        if name != 'SRWLOptD' or i == len(obj_arOpt) - 1:  # drifts are not included in the list, except the last drift
            counter += 1

            data = []
            title = ''
            elem_type = ''

            if name == 'SRWLOptA':
                key = 'S'
                names[key] += 1
                elem_type = 'aperture'

            elif name == 'SRWLOptT':
                # Check the type based on focal lengths of the element:
                if obj_arOpt[i].Fx > 1e20 and obj_arOpt[i].Fy > 1e20:  # mirror, no surface curvature
                    key = 'HDM'
                    elem_type = 'mirror'

                elif (obj_arOpt[i].Fx > 1e20 and obj_arOpt[i].Fy < 1e20) or \
                        (obj_arOpt[i].Fx < 1e20 and obj_arOpt[i].Fy > 1e20):  # CRL
                    key = 'CRL'
                    names[key] += 1
                    elem_type = 'crl'

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


def propagation(op):
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
                prop_dict[unicode(str(counter))].append(default_drift_prop)

    return prop_dict


python_dict = {
    u'models': {
        u'beamline': beamline(op.arOpt, v.op_r),
        u'electronBeam': {
            u'beamSelector': unicode(v.ebm_nm),  # u'NSLS-II Low Beta Day 1',
            u'current': v.ebm_i,  # 0.5,
            u'energy': app.ueb_e,  # 3,
            u'energyDeviation': v.ebm_de,  # 0,
            u'horizontalAlpha': app.ueb_alpha_x,  # 0,
            u'horizontalBeta': app.ueb_beta_x,  # 2.02,
            u'horizontalDispersion': app.ueb_eta_x,  # 0,
            u'horizontalDispersionDerivative': app.ueb_eta_x_pr,  # 0,
            u'horizontalEmittance': app.ueb_emit_x * 1e9,  # 0.9,
            u'horizontalPosition': v.ebm_x,  # 0,
            u'isReadOnly': True,
            u'name': unicode(v.ebm_nm),  # u'NSLS-II Low Beta Day 1',
            u'rmsSpread': app.ueb_sig_e,  # 0.00089,
            u'verticalAlpha': app.ueb_alpha_y,  # 0,
            u'verticalBeta': app.ueb_beta_y,  # 1.06,
            u'verticalDispersion': app.ueb_eta_y,  # 0,
            u'verticalDispersionDerivative': app.ueb_eta_y_pr,  # 0,
            u'verticalEmittance': app.ueb_emit_y * 1e9,  # 0.008,
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
        u'gaussianBeam': {
            u'energyPerPulse': app.gb_energy_per_pulse,  # u'0.001',
            u'polarization': app.gb_polarization,  # 1,
            u'rmsPulseDuration': app.gb_rms_pulse_duration * 1e12,  # 0.1,
            u'rmsSizeX': app.gb_rms_size_x * 1e6,  # u'9.78723',
            u'rmsSizeY': app.gb_rms_size_y * 1e6,  # u'9.78723',
            u'waistAngleX': app.gb_waist_angle_x,  # 0,
            u'waistAngleY': app.gb_waist_angle_y,  # 0,
            u'waistX': app.gb_waist_x,  # 0,
            u'waistY': app.gb_waist_y,  # 0,
            u'waistZ': app.gb_waist_z,  # 0,
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
        u'multipole': {
            u'distribution': unicode(app.mp_distribution),  # u'n',
            u'field': app.mp_field,  # 0.4,
            u'length': app.mp_len,  # 3,
            u'order': app.mp_order,  # 1,
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
        u'propagation': propagation(op),
        u'simulation': {
            u'facility': unicode(v.name.split()[0]),  # u'NSLS-II',
            u'horizontalPointCount': v.w_nx,  # 100,
            u'isExample': 0,  # u'1',
            u'name': unicode(v.name),  # u'NSLS-II CHX beamline',
            u'photonEnergy': v.w_e,  # u'9000',
            u'sampleFactor': v.w_smpf,  # 1,
            u'simulationId': None,  # u'1YA8lSnj',
            u'sourceType': app.source_type,  # u'u',
            u'verticalPointCount': v.w_ny,  # 100
        },
        u'sourceIntensityReport': srw_default['models']['sourceIntensityReport'],
        u'undulator': {
            u'horizontalAmplitude': v.und_bx,  # u'0',
            u'horizontalInitialPhase': v.und_phx,  # 0,
            u'horizontalSymmetry': v.und_sx,  # 1,
            u'length': v.und_len,  # u'3',
            u'longitudinalPosition': v.und_zc,  # 0,
            u'period': v.und_per * 1e3,  # u'20',
            u'verticalAmplitude': v.und_by,  # u'0.88770981',
            u'verticalInitialPhase': v.und_phy,  # 0,
            u'verticalSymmetry': v.und_sy,  # -1
        },
        u'watchpointReport': {
            u'characteristic': None,  # 0,
            u'horizontalPosition': None,  # 0,
            u'horizontalRange': None,  # u'0.4',
            u'polarization': None,  # 6,
            u'precision': None,  # 0.01,
            u'verticalPosition': None,  # 0,
            u'verticalRange': None,  # u'0.6',
        },
    },
    u'report': u'',  # u'powerDensityReport',
    u'simulationType': u'srw',
    u'version': unicode(schema_common['version']),  # u'20160120',
}

pprint.pprint(python_dict)

print()
