
from pathlib import Path
import shutil

# import unittest.mock as mock
import pytest
from _pytest.monkeypatch import MonkeyPatch

import fix_imports
from dbs import DB_auth, DB_keys, DB_password
import pm_ui
from pm_ui import PM_UI
from pm_class import PM
from db_general import DB_general
from file_handling import generate_salt, get_salt
import file_locations
import crypto_stuff


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


@pytest.fixture(scope='class')
def default_paths(paths):
    def_paths = get_paths_from_str(paths, 0)
    # make sure the files exist
    if not def_paths[0].exists():
        generate_salt(def_paths[0])
    for path in def_paths[1:]:
        if not path.exists():
            DB_general(path)
    yield def_paths
    # remove files after some time
    for path in def_paths:
        if path.exists():
            path.unlink()

@pytest.fixture(scope='class')
def normal_paths(paths, default_paths):
    norm_paths = get_paths_from_str(paths, 1)
    # make sure the files exist
    if not norm_paths[0].exists():
        generate_salt(norm_paths[0])
    for path, def_path in zip(norm_paths[1:], default_paths[1:]):
        if not path.exists():
            shutil.copy(def_path.resolve(), path.resolve())
    yield norm_paths
    for path in norm_paths:
        if path.exists():
            path.unlink()




class TestInit():

    @pytest.mark.parametrize(
        'answers', ['y', 'n']
    )
    def test_init_from_nothing(self, monkeypatch, paths, answers):
        def answer(question=None):
            return answers
        
        monkeypatch.setattr(pm_ui, 'yes_or_no_question', answer)
        monkeypatch.setattr(file_locations, 'paths', paths)

        # pm = PM_UI()
        if answers == 'n':
            assert PM_UI().pm is None
        elif answers == 'y':
            def pwd(prompt=None):
                return 'password'
            monkeypatch.setattr(pm_ui, 'get_master_password', pwd)
            assert isinstance(PM_UI().pm, PM)

    @pytest.mark.parametrize(
        'answers', [
            ('y', None), 
            ('n', 'n'),
            ('n', 'y')]
    )
    def test_init_with_default(self, monkeypatch, paths, answers, default_paths):
        count = [-1]
        def answer(question=None):
            count[0] += 1
            return answers[count[0]]
        
        monkeypatch.setattr(pm_ui, 'yes_or_no_question', answer)
        monkeypatch.setattr(file_locations, 'paths', paths)

        if answers[0] == 'y':
            pmui = PM_UI()

            # now we should have a PM object
            assert isinstance(pmui.pm, PM)
            # and filepaths should be default paths
            assert pmui.pm.dba.filepath.resolve() == default_paths[1].resolve()
            assert pmui.pm.dbk.filepath.resolve() == default_paths[2].resolve()
            assert pmui.pm.dbp.filepath.resolve() == default_paths[3].resolve()
        elif answers[1] == 'n':
            assert PM_UI().pm is None
        else:
            def pwd(prompt=None):
                return 'password'
            monkeypatch.setattr(pm_ui, 'get_master_password', pwd)
            pmui = PM_UI()

            # now we should have a PM object
            assert isinstance(pmui.pm, PM)
            # and filepaths should be default paths
            assert pmui.pm.dba.filepath.resolve() == default_paths[1].resolve()
            assert pmui.pm.dbk.filepath.resolve() == default_paths[2].resolve()
            assert pmui.pm.dbp.filepath.resolve() == default_paths[3].resolve()
        
    
    def test_reconnect(self, monkeypatch, paths, default_paths):
        monkeypatch.setattr(file_locations, 'paths', paths)

        def say_no(q=None):
            return 'n'
        monkeypatch.setattr(pm_ui, 'yes_or_no_question', say_no)
        # at first we do not connect with normal paths
        pmui = PM_UI()

        assert pmui.pm is None

        # make normal files available
        norm_paths = get_paths_from_str(paths, 1)
        for path, def_path in zip(norm_paths, default_paths):
            assert not path.exists()
            assert def_path.exists()
            shutil.copy(def_path.resolve(), path.resolve())
        # reconnect with normal files
        pmui.reconnect()
        # now we are connected to normal files
        assert isinstance(pmui.pm, PM)
        assert pmui.pm.dba.filepath.resolve() == norm_paths[1].resolve()
        

    def test_init_with_normal(self, monkeypatch, paths, normal_paths):
        monkeypatch.setattr(file_locations, 'paths', paths)

        # we should get a PM object with normal paths
        pmui = PM_UI()
        assert isinstance(pmui.pm, PM)
        assert pmui.pm.dba.filepath.resolve() == normal_paths[1].resolve()
        assert pmui.pm.dbk.filepath.resolve() == normal_paths[2].resolve()
        assert pmui.pm.dbp.filepath.resolve() == normal_paths[3].resolve()


@pytest.fixture(scope='module')
def master_password():
    return '5up3r_g00d_p4s5w0r|)'

@pytest.fixture(scope='class')
def monkeyclass():
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope='class')
def pmui_empty(monkeyclass, paths, normal_paths, master_password):
    # create 'empty' dbs
    argmts = (get_salt(normal_paths[0]), DB_auth(normal_paths[1]), DB_keys(normal_paths[2]), DB_password(normal_paths[3]))
    PM(*argmts)
    # 
    monkeyclass.setattr(file_locations, 'paths', paths)
    pmui = PM_UI()
    pmui.pm.add_master_password(master_password)
    pmui.pm.set_name_lists()
    return pmui

class TestPMUIempty():

    def test_get_unique_info_from_user(self, pmui_empty, monkeypatch):
        info = ('username', 'email', 'app', 'url')
        def get_info():
            return info
        monkeypatch.setattr(pm_ui, 'get_info_from_user', get_info)

        # since pm dbs are 'empty', info is unique
        assert pmui_empty.get_unique_info_from_user() == info


    def test_find_app_and_username(self, pmui_empty, monkeypatch, capsys):
        first_line = crypto_stuff.generate_password()
        name_of_the_app = crypto_stuff.generate_password()
        def app_name(*args):
            return name_of_the_app
        monkeypatch.setattr('builtins.input', app_name)

        # there is nothing so this should find nothing
        assert pmui_empty.find_app_and_username(first_line) is None
        printed = capsys.readouterr()[0]
        assert first_line in printed
        assert f'No passwords related to {name_of_the_app} found' in printed

    def test_find_password_for_app(self, pmui_empty, monkeypatch, capsys):
        name_of_the_app = crypto_stuff.generate_password()
        def app_name(*args):
            return name_of_the_app
        
        def error_message(*args):
            print('ERROR')

        monkeypatch.setattr('builtins.input', app_name)
        # if obtain_password is called, something has gone wrong
        monkeypatch.setattr(pm_ui, 'obtain_password', error_message)
        
        assert pmui_empty.find_password_for_app() is None
        printed = capsys.readouterr()[0]

        assert 'Email' not in printed
        assert 'Username' not in printed
        assert 'ERROR' not in printed

    def test_save_password_to_db_or_not(self, pmui_empty):
        assert isinstance(pmui_empty.pm, PM)

    def test_add_password(self, pmui_empty):
        assert isinstance(pmui_empty.pm, PM)


@pytest.fixture(scope='class')
def pmui_w_stuff(pmui_empty):
    # add some info
    return pmui_empty



class TestPMUI():


    def test_get_unique_info_from_user(self):
        pass

    def test_find_app_and_username(self):
        pass

    def test_find_password_for_app(self):
        pass

    def test_save_password_to_db_or_not(self):
        pass

    def test_change_password_in_db_or_not(self):
        pass

    def test_add_password(self):
        pass

    def test_change_password_in_db(self):
        pass

    def test_change_password(self):
        pass

    def test_change_password_info(self):
        pass

    def test_delete_password(self):
        pass