from pathlib import Path

import pytest
import pyperclip

import fix_imports

import file_locations
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
    # # make sure the files exist
    # if not def_paths[0].exists():
    #     generate_salt(def_paths[0])
    # for path in def_paths[1:]:
    #     if not path.exists():
    #         DB_general(path)
    yield def_paths
    # remove files after some time
    for path in def_paths:
        if path.exists():
            path.unlink()


@pytest.fixture(scope='module')
def pm_empty(paths):
    pass


def test_end_prompt(monkeypatch, capsys):
    pyperclip.copy('important text in clipboard')
    monkeypatch.setattr(pm.getpass, 'getpass', lambda *args: None)

    pm.end_prompt()
    expected_text = '\n\n'

    assert capsys.readouterr()[0] == expected_text

    assert pyperclip.paste() == 'nothing here'


# @pytest.mark.parametrize(
#     'inputs', [
#         'y',
#         password,
#         password,
#         '1',
#         'Very Distinctive App',
#         'url.of.app',
#         'username',
#         'e@mail.com',
#         '2',
#         '0',
#         'y',
#         'y',
#         None,
#         '5',
#         None,
#         '0',
#         'y'
#     ]
# )
def test_password_manager_clean_start(monkeypatch, capsys, paths, password, default_paths):
    app_name = crypto_stuff.generate_password(10, True)
    pw = '1234'
    inputs = ['y', password, password, '1', app_name, 'url.of.app', 'username', 'e@mail.com', '2', '0', 'y', 'y', None, '5', None, '0', 'y']
    monkeypatch.setattr(file_locations, 'paths', paths)
    count = [-1]

    def give_input(prompt=None):
        count[0] += 1
        print(f' input prompt: {prompt} ')
        print(f' input number: {count[0]} ')
        print(f' inputted value: {inputs[count[0]]} ')

        return inputs[count[0]]

    monkeypatch.setattr('builtins.input', give_input)
    monkeypatch.setattr(pm.getpass, 'getpass', give_input)

    pm.password_manager()

    assert app_name in capsys.readouterr()[0]