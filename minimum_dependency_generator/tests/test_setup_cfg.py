import sys
import tempfile

import pytest
from packaging.specifiers import Specifier

from ..minimum_dependency_generator import (
    generate_min_requirements,
    parse_setup_cfg
)

def test_with_setup_cfg(
    dask_dep, pandas_dep, woodwork_dep, numpy_lower, ploty_dep, numpy_upper, setuptools, p_ytest_dep
):
    setup_cfg_str = f'''\
    [metadata]
    name = example_package

    [options]
    install_requires =
        {dask_dep}
        {pandas_dep}
        {woodwork_dep}
        {numpy_lower}
    setup_requires =
        {setuptools}

    [options.extras_require] =
    koalas =
        {ploty_dep}
        {numpy_upper}
    test =
        {p_ytest_dep}
    '''
    start_of_file = ['[metadata]', 'name = example_package', " ", '[options]', 'install_requires =']
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".cfg", prefix="setup"
    ) as setup_cfg_f:
        setup_cfg_f.write(setup_cfg_str)
        setup_cfg_f.flush()

        paths = [setup_cfg_f.name]
        options = ['install_requires', 'setup_requires']
        extra_requires = ['koalas', 'test']
        min_requirements = generate_min_requirements(paths, options, extra_requires)
    assert '-r' not in min_requirements
    assert '.txt' not in min_requirements
    assert 'core-requirements.txt' not in min_requirements
    min_requirements = min_requirements.split('\n')
    assert min_requirements[-1] == ''
    min_requirements = min_requirements[:-1]
    expected_min_reqs = [
        "dask[dataframe]==2.30.0",
        "pandas==0.24.1",
        "woodwork==0.0.11",
        "numpy==1.15.4",
        "setuptools==47",
        "plotly==4.14.0",
        "pytest==5.2.0"
    ]
    assert len(min_requirements) == len(expected_min_reqs)
    for idx, min_req in enumerate(min_requirements):
        assert expected_min_reqs[idx] == min_req.strip()