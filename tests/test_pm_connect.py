from pathlib import Path
import os

import pytest

import fix_imports
from dbs import DB_general
import pm_connect as pmc


@pytest.fixture(scope='module')
def salt():
    return os.urandom(16)

@pytest.fixture(scope='module')
def paths():
    return (('tests/salt_test.txt', 'tests/salt_test2.txt'),
            ('tests/test_auth.db', 'tests/test_auth2.db'),
            ('tests/test_keys.db', 'tests/test_keys2.db'),
            ('tests/test_data.db', 'tests/test_data2.db'))


@pytest.fixture(scope='module')
def default_paths(paths):
    d_paths = [path[0] for path in paths]
    # default_paths = (Path(__file__).parent / 'test_auth.db', Path(__file__).parent / 'test_keys.db', Path(__file__).parent / 'test_data.db')
    def_paths = tuple(Path(__file__).parent / path.split('/')[1] for path in d_paths)
    yield def_paths
    for path in def_paths:
        if path.exists():
            path.unlink()

@pytest.fixture(scope='module')
def normal_paths(paths):
    n_paths = [path[1] for path in paths]
    norm_paths = tuple(Path(__file__).parent / path.split('/')[1] for path in n_paths)
    yield norm_paths
    for path in norm_paths:
        if path.exists():
            path.unlink()



def test_connect_to_pm_dbs_no_exist(monkeypatch):
    # if get_files returns just False for existence
    def files(*args):
        return (tuple(None for _ in range(4)), False)
    
    monkeypatch.setattr(pmc, 'get_files', files)

    assert pmc.connect_to_pm_dbs(False, False) is None


def test_connect_to_pm_dbs_force_connect(monkeypatch, salt, default_paths):
    def files(*args):
        return ((salt, *(default_paths[1:])), True)
    
    monkeypatch.setattr(pmc, 'get_files', files)

    pm = pmc.connect_to_pm_dbs(True, True)

    assert isinstance(pm, pmc.PM)


# connecting to default files
def test_connect_to_pm_dbs_default(monkeypatch, paths):

    monkeypatch.setattr(pmc.fl, 'paths', paths)

    # make sure the default paths exist, so that we can connect to them
    paths = pmc.get_files(pmc.fl.paths)[0][1:]
    for path in paths:
        if not path.exists():
            DB_general(path)
    assert isinstance(pmc.connect_to_pm_dbs(), pmc.PM)


def test_connect_to_pm_dbs(monkeypatch, paths, normal_paths, default_paths):
    monkeypatch.setattr(pmc.fl, 'paths', paths)

    # make sure the files exist
    if not normal_paths[0].exists():
        default_paths[0].replace(normal_paths[0])
    for path in normal_paths[1:]:
        if not path.exists():
            DB_general(path)
    
    assert isinstance(pmc.connect_to_pm_dbs(False, False), pmc.PM)
