import os
from pathlib import Path

import pytest

import fix_imports
import file_handling as fh


# This is very system specific, at least for now


# some filenames
@pytest.fixture
def filepaths():
    paths = ('test_salt.txt', 'test_a.db', 'test_k.db', 'test_d.db')
    yield paths
    for path in paths:
        if Path(path).exists():
            Path(path).unlink()


def test_salt():
    file = Path('test_salt.txt')
    salt = fh.generate_salt(file)
    assert isinstance(salt, bytes)
    assert len(salt) == 16
    salt2 = fh.get_salt(file)
    assert isinstance(salt2, bytes)
    assert salt == salt2
    file.unlink()


# I only have the C drive
def test_get_drives():
    if os.name == 'nt':
        assert 'C:' in fh.get_drives()
    else:
        assert '/' in fh.get_drives()

def test_get_possible_starting_folders():
    folders = fh.get_possible_starting_folders()
    if os.name == 'nt':
        assert Path('C:/users/public') in folders
        assert Path('C:/Program Files') in folders
    else:
        username = os.environ['USER']
        assert Path(f'/home/{username}') in folders

def test_find_path():
    filepath = 'tests/test_file_handling.py'
    assert fh.find_path(filepath) == Path(__file__).resolve()
    filepath = 'tests/not existing file.ext'
    assert fh.find_path(filepath) is None

def test_find_path_from_list():
    path_list = ('tests/not existing file.ext', 'tests/test_file_handling.py')
    assert fh.find_path_from_list(path_list) == Path(__file__).resolve()

def test_get_files(filepaths):
    salt_f = filepaths[0]
    # types = ('a', 'k', 'd')
    # some nonexistent files
    no_exist = 'test_not_exist.txt'
    db_a = filepaths[1]
    db_k = filepaths[2]
    db_d = filepaths[3]
    paths = ((salt_f,), (no_exist, f'tests/{db_a}'), (no_exist, f'tests/{db_k}'), (no_exist, f'tests/{db_d}'))
    files = fh.get_files(paths)
    assert not files[1]
    assert files[0][1:] == tuple(Path(no_exist) for _ in range(3))
    assert len(files[0][0]) == 16

    # what if files did exists
    salt = fh.generate_salt(salt_f)
    for file in filepaths[1:]:
        f = open(file, 'w')
        f.close()
    files = fh.get_files(paths)
    assert files[1]
    assert files[0][0] == salt
    assert files[0][1:] == tuple(Path(file).resolve() for file in filepaths[1:])
