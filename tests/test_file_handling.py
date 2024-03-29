import os
from pathlib import Path

import pytest

import fix_imports
import file_handling as fh


# This is very system specific, at least for now


# some filenames
@pytest.fixture
def filepaths():
    paths0 = ('test_salt.txt', 'test_a.db', 'test_k.db', 'test_d.db')
    paths = tuple(str(Path(__file__).parent / p) for p in paths0)
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
        assert 'C:/' in fh.get_drives()
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
    # passwordmanager folder should always be here
    assert Path(__file__).parent.parent in folders

@pytest.mark.parametrize(
    'filepath, result', [
        ('tests/test_file_handling.py', Path(__file__).resolve()),
        ('tests/not existing file.ext', None)
    ]
)
def test_find_path(filepath, result):
    assert fh.find_path(filepath) == result
    # filepath = 'tests/not existing file.ext'
    # assert fh.find_path(filepath) is None

@pytest.mark.parametrize(
    'filepath, name', [
        ('windows', 'nt'),
        ('C:/users', 'nt'),
        ('home', None),
        ('/dev', None)
    ]
)
def test_find_path_sys(filepath, name):
    os_name = 'nt' if os.name == 'nt' else None
    if os_name == name:
        assert fh.find_path(filepath)



def test_find_path_from_list():
    path_list = ('tests/not existing file.ext', 'tests/test_file_handling.py')
    assert fh.find_path_from_list(path_list) == (Path(__file__).resolve(), 1)

def test_find_all_paths_from_list():
    path_list = ('tests/not existing file.ext', 'tests/test_file_handling.py', 'file_handling.py')
    assert fh.find_all_paths_from_list(path_list) == ((Path(__file__).resolve(), 1), (Path(__file__).parent.parent.resolve() / 'file_handling.py', 2))


def test_get_files(filepaths):
    salt_f = filepaths[0]
    # some nonexistent files
    no_exist = Path(__file__).parent / 'test_not_exist.txt'
    paths = ((salt_f,), (no_exist, filepaths[1]), (no_exist, filepaths[2]), (no_exist, filepaths[3]))
    files = fh.get_files(paths)
    assert not files[1]
    assert files[0][1:] == tuple(Path(no_exist) for _ in range(3))
    # assert files[2] == (0, 0, 0, 0)
    assert len(files[0][0]) == 16

    # what if files did exist
    salt = fh.generate_salt(salt_f)
    for file in filepaths[1:]:
        f = open(file, 'w')
        f.close()
    files = fh.get_files(paths)
    # now we should find files
    assert files[1]
    assert files[0][0] == salt
    assert files[0][1:] == tuple(Path(file).resolve() for file in filepaths[1:])
    # assert files[2] == (0, 1, 1, 1)
