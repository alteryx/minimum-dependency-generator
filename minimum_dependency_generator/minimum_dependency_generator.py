import configparser
import os
from collections import defaultdict

from packaging.requirements import Requirement
from packaging.specifiers import Specifier

from .utils import (
    clean_cfg_section,
    create_strict_min,
    determine_package_name,
    find_operator_version,
    is_requirement_path,
    remove_comment,
    verify_list,
    verify_python_environment
)


def find_min_requirement(requirement, python_version="3.7", major_python_version="py3"):
    if is_requirement_path(requirement):
        # skip requirement paths
        # ex '-r core_requirements.txt'
        return
    requirement = remove_comment(requirement)
    if not verify_python_environment(requirement):
        return
    if ">=" in requirement:
        # mininum version specified (ex - 'package >= 0.0.4')
        package = Requirement(requirement)
        version = find_operator_version(package, ">=")
        mininum = create_strict_min(version)
    elif "==" in requirement:
        # version strictly specified
        package = Requirement(requirement)
        version = find_operator_version(package, "==")
        mininum = create_strict_min(version)
    else:
        # mininum version not specified (ex - 'package < 0.0.4')
        # version not specified (ex - 'package')
        raise ValueError(
            "Operator does not exist or is an invalid operator. Please specify the mininum version."
        )
    name = determine_package_name(package)
    min_requirement = Requirement(name + str(mininum))
    return min_requirement


def parse_requirements_text_file(paths):
    requirements = []
    if isinstance(paths, list) and ' ' in paths[0]:
        paths = paths[0].split(' ')

    for path in paths:
        with open(path) as f:
            requirements.extend(f.readlines())
    return requirements


def parse_setup_cfg(paths, options, extras_require):
    config = configparser.ConfigParser()
    config.read(paths[0])

    requirements = []
    if options:
        options = verify_list(options)
        for option in options:
            requirements += clean_cfg_section(config['options'][option])
    if extras_require:
        options = verify_list(options)
        for extra in extras_require:
            requirements += clean_cfg_section(config['options.extras_require'][extra])
    return requirements


def generate_min_requirements(paths, options=None, extras_require=None):
    is_requirements_text = False
    requirements_to_specifier = defaultdict(list)
    min_requirements = []

    if len(paths) == 1 and paths[0].endswith('.cfg') and os.path.basename(paths[0]).startswith('setup'):
        requirements = parse_setup_cfg(paths, options, extras_require)
    else:
        is_requirements_text = True
        requirements = parse_requirements_text_file(paths)

    for req in requirements:
        if is_requirement_path(req):
            # skip requirement paths
            # ex '-r core_requirements.txt'
            continue
        package = Requirement(remove_comment(req))
        name = determine_package_name(package)
        if name in requirements_to_specifier:
            prev_req = Requirement(requirements_to_specifier[name])
            new_req = prev_req.specifier & package.specifier
            requirements_to_specifier[name] = name + str(new_req)
        else:
            requirements_to_specifier[name] = name + str(package.specifier)

    for req in list(requirements_to_specifier.values()):
        min_package = find_min_requirement(req)
        min_requirements.append(str(min_package))
    min_requirements = '\n'.join(min_requirements) + '\n'
    return min_requirements
