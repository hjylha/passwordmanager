from pathlib import Path
import os
import getpass
if os.name == 'nt':
    import msvcrt
else:
    import select

import pytest
import pyperclip

import fix_imports

import file_locations
from file_handling import generate_salt, get_salt
from pm_class import PM, DB_auth, DB_keys, DB_password
import pm
import crypto_stuff


@pytest.fixture(scope='module')
def password():
    return crypto_stuff.generate_password(32, True)


@pytest.fixture(scope='module')
def paths():
    return (('tests/salt_test.txt', 'tests/salt_test2.txt'),
            ('tests/test_auth.db', 'tests/test_auth2.db'),
            ('tests/test_keys.db', 'tests/test_keys2.db'),
            ('tests/test_data.db', 'tests/test_data2.db'))

# get default or normal paths from paths
def get_paths_from_str(paths_as_str, index):
    paths_to_look_at = [path[index] for path in paths_as_str]
    return tuple(Path(__file__).parent / path.split('/')[1] for path in paths_to_look_at)

@pytest.fixture(scope='module')
def default_paths(paths):
    def_paths = get_paths_from_str(paths, 0)
    yield def_paths
    # remove files after some time
    for path in def_paths:
        if path.exists():
            path.unlink()

@pytest.fixture(scope='module')
def normal_paths(paths):
    norm_paths = get_paths_from_str(paths, 1)
    yield norm_paths
    # remove files after some time
    for path in norm_paths:
        if path.exists():
            path.unlink()


@pytest.fixture(scope='module')
def pm_empty(normal_paths):
    if not normal_paths[0].exists():
        generate_salt(normal_paths[0])
    argmts = (get_salt(normal_paths[0]), DB_auth(normal_paths[1]), DB_keys(normal_paths[2]), DB_password(normal_paths[3]))
    return PM(*argmts)


@pytest.fixture(scope='module')
def some_info():
    return [(f'user{i}', f'email{i}@d.c', f'App{i}', f'www.app{i}.com') for i in range(13)]


@pytest.fixture(scope='module')
def pm_w_stuff(pm_empty, some_info):
    # add some info
    infos = [(*info[:2], f'password{i}', *info[2:]) for i, info in enumerate(some_info)]
    for info in infos:
        pm_empty.force_add_password(*info)
    return pm_empty


# onto testing
@pytest.mark.parametrize(
    'inputs', [
        ['y', '1', 'url.of.app', 'username', 'e@mail.com', '2', '0', 'y', 'y', '5', '0', 'y']
    ]
)
def test_password_manager_clean_start(monkeypatch, capsys, paths, password, default_paths, inputs):
    inputs.insert(1, password)
    inputs.insert(1, password)
    # random app_name should be noticeable
    app_name = crypto_stuff.generate_password(10, True)
    inputs.insert(4, app_name)

    monkeypatch.setattr(file_locations, 'paths', paths)
    # clearing screen might be bad for debugging
    monkeypatch.setattr(pm, 'clear_screen', lambda: None)
    if os.name == 'nt':
        monkeypatch.setattr(msvcrt, 'kbhit', lambda *args: True)
        monkeypatch.setattr(msvcrt, 'getch', lambda *args: b'\r')
    else:
        monkeypatch.setattr(select, 'select', lambda *args: (False, None, None))

    count = [-1]

    def give_input(prompt=None):
        count[0] += 1
        return inputs[count[0]]

    monkeypatch.setattr('builtins.input', give_input)
    monkeypatch.setattr(getpass, 'getpass', give_input)

    pm.password_manager()

    assert app_name in capsys.readouterr()[0]