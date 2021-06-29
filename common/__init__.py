import sys
import winreg
import json
from pathlib import Path
from pkgutil import iter_modules
from platform import system

# Third party imports
import numpy as np
from si_prefix import si_parse

FLOATING_POINT_REGEX = r'[-+]?\d*\.\d+|[-+]?\d+'


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def get_class_from_string(name):
    components = name.split('.')
    module = __import__(components[0])
    for component in components[1:]:
        module = getattr(module, component)

    return module


def get_object_class_name(instance):
    type_info = type(instance)
    return f'{type_info.__module__}.{type_info.__name__}'


# Prints a standardized repr of an object
def get_repr(instance):
    return f"<{get_object_class_name(instance)} {', '.join(f'{k}={repr(v)}' for k, v in instance.__dict__.items())}>"


# Get absolute path of resource (works both for dev and PyInstaller)
def resource_path(relative_path):
    base_path = Path(getattr(sys, '_MEIPASS', Path(sys.argv[0]).resolve().parent))
    return base_path / relative_path


def find_modules(module_path):
    module_path = '/'.join(module_path.split('.'))
    for package in iter_modules([module_path]):
        if package.ispkg:
            yield from find_modules(f'{module_path}/{package.name}')

    yield '.'.join(module_path.split('/'))


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False


def parse_si_input(input):
    # Parse SI prefixes
    input = si_parse(input.rstrip('.'))
    # Kinda hacky way of determining if a value was originally an integer, as si_parse will always return float
    # But it works ¯\_(ツ)_/¯
    return int(input) if int(input) == input else input


def clamp(n, lower, upper):
    return max(lower, min(n, upper))


def get_reg_key(reg_path, name):
    value = None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, name)
    except WindowsError:
        pass

    return value


# TODO: Adapt for platforms other than Windows
def get_license_key(app_publisher, app_name):
    reg_path = '\\'.join(['SOFTWARE', app_publisher, app_name])
    return get_reg_key(reg_path, 'LicenseKey')


def get_config_path(app_publisher, app_name):
    home = Path.home()

    # If running on Windows, return Documents folder
    # TODO: Account for systems with Documents in a location other than the C drive
    if system() == 'Windows':
        home /= 'Documents'

    return home / app_publisher / app_name


# Converts the table column arrays into one master step list
def convert_to_sweep(starting_values, ending_values, step_size_values, num_steps_values, num_steps_last_edited,
                     repeat_pulses=1):
    step_list = np.array([])  # Creates list that steps will go into
    # Use concatenate to add the separate arrays together into one master step list
    for i in range(len(starting_values)):
        if num_steps_last_edited[i]:
            try:
                step_list = np.concatenate(
                    (step_list, np.linspace(starting_values[i], ending_values[i], num_steps_values[i])))
            except TypeError:
                continue
        else:
            try:
                num_points = int((ending_values[i] - starting_values[i]) / step_size_values[i])
                end_point = starting_values[i] + (num_points * step_size_values[i])
                step_list = np.concatenate(
                    (step_list, np.linspace(starting_values[i], end_point, num_points + 1)))
            except (TypeError, IndexError, ValueError) as e:
                continue

    # Before adding in repeat pulses organize the step list numerically from small to large and remove duplicates
    step_list = np.unique(step_list)

    # Finally add repeat pulses to the list, if set to 1 this line has no effect
    step_list = np.repeat(step_list, repeat_pulses, axis=0)

    return step_list


def define_opposite_sweep_generators(starting_values, ending_values, step_size_values, num_steps_values,
                                     num_steps_last_edited):
    for i in range(len(starting_values)):
        if num_steps_last_edited[i]:

            try:
                # Create the step_list with the num steps method,
                # using the step size from that array create the other array
                step_list_1, step_size = np.linspace(starting_values[i], ending_values[i], num_steps_values[i],
                                                     retstep=True)
                step_list_1 = np.unique(step_list_1)

                step_list_2 = np.arange(starting_values[i], ending_values[i], step_size)
                step_list_2 = np.append(step_list_2, ending_values[i])
                step_list_2 = np.unique(step_list_2)

                # If the arrays turn out to be equal save the step_size value, else set a new value to display
                if np.allclose(step_list_1, step_list_2):
                    step_size_values[i] = step_size
                else:
                    step_size_values[i] = '-'
            except (RecursionError, ValueError, TypeError, IndexError):
                step_size_values[i] = '-'
        else:
            try:
                # Create the step_list with the step size method,
                # using the step size from that array create the other array
                num_points = int((ending_values[i] - starting_values[i]) / step_size_values[i])
                end_point = starting_values[i] + (num_points * step_size_values[i])
                step_list_2 = np.linspace(starting_values[i], end_point, num_points + 1)
                step_list_2 = np.unique(step_list_2)

                # If the arrays turn out to be equal save the step_size value, else set a new value to display
                num_steps_values[i] = step_list_2.size

            except (RecursionError, ValueError, TypeError, IndexError):
                num_steps_values[i] = '-'

    return step_size_values, num_steps_values
