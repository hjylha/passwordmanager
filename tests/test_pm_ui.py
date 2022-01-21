
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
        
        monkeypatch.setattr(pm_ui, 'yes_or_no_question', lambda *args: answers)
        monkeypatch.setattr(file_locations, 'paths', paths)

        # pm = PM_UI()
        if answers == 'n':
            assert PM_UI().pm is None
        elif answers == 'y':
            monkeypatch.setattr(pm_ui, 'get_master_password', lambda *args: 'password')
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
            monkeypatch.setattr(pm_ui, 'get_master_password', lambda *args: 'password')
            pmui = PM_UI()

            # now we should have a PM object
            assert isinstance(pmui.pm, PM)
            # and filepaths should be default paths
            assert pmui.pm.dba.filepath.resolve() == default_paths[1].resolve()
            assert pmui.pm.dbk.filepath.resolve() == default_paths[2].resolve()
            assert pmui.pm.dbp.filepath.resolve() == default_paths[3].resolve()
        
    
    def test_reconnect(self, monkeypatch, paths, default_paths):
        monkeypatch.setattr(file_locations, 'paths', paths)
        # we do not use defaults nor initialize pm dbs
        monkeypatch.setattr(pm_ui, 'yes_or_no_question', lambda *args: 'n')
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

# need to use monkeypatch in a wider scope
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
    # change the filepaths for PM_UI
    monkeyclass.setattr(file_locations, 'paths', paths)
    pmui = PM_UI()
    pmui.pm.add_master_password(master_password)
    pmui.pm.set_name_lists()
    return pmui

class TestPMUIempty():

    def test_get_unique_info_from_user(self, pmui_empty, monkeypatch):
        info = ('username', 'email', 'app', 'url')
        monkeypatch.setattr(pm_ui, 'get_info_from_user', lambda: info)

        # since pm dbs are 'empty', info is unique
        assert pmui_empty.get_unique_info_from_user() == info


    def test_find_app_and_username(self, pmui_empty, monkeypatch, capsys):
        # random header line
        first_line = crypto_stuff.generate_password()
        # 'input' random app name
        name_of_the_app = crypto_stuff.generate_password()
        monkeypatch.setattr('builtins.input', lambda *args: name_of_the_app)

        # there is nothing so this should find nothing
        assert pmui_empty.find_app_and_username(first_line) is None
        printed = capsys.readouterr()[0]
        assert first_line in printed
        assert f'No passwords related to {name_of_the_app} found' in printed

    def test_find_password_for_app(self, pmui_empty, monkeypatch, capsys):
        # 'input' random app name
        name_of_the_app = crypto_stuff.generate_password()
        monkeypatch.setattr('builtins.input', lambda *args: name_of_the_app)
        # if obtain_password is called, something has gone wrong
        def error_message(*args):
            print('ERROR')
        monkeypatch.setattr(pm_ui, 'obtain_password', error_message)
        
        assert pmui_empty.find_password_for_app() is None
        printed = capsys.readouterr()[0]

        assert 'Email' not in printed
        assert 'Username' not in printed
        assert 'ERROR' not in printed

    @pytest.mark.parametrize(
        'ans, is_done, text', [
            (('y', 'y', None), True, 'saved to the database'),
            (('n', 'y', None), False, None),
            (('n', 'n', None), True, 'Adding password canceled.'),
            (('y', 'n', 'y'), False, None),
            (('y', 'n', 'n'), True, 'Adding password canceled.')
        ]
    )
    def test_save_password_to_db_or_not(self, pmui_empty, monkeypatch, capsys, ans, is_done, text):
        info = tuple(crypto_stuff.generate_password() for _ in range(5))
        count = [-1]
        def answer(*args):
            count[0] += 1
            return ans[count[0]]
        
        monkeypatch.setattr(pm_ui, 'yes_or_no_question', answer)

        assert pmui_empty.save_password_to_db_or_not(info) == is_done
        
        if text:
            printed = capsys.readouterr()[0]
            assert text in printed
        
        if ans[:2] == ('y', 'y'):
            pw_info = pmui_empty.pm.find_password(info[3])
            assert len(pw_info) == 1
            # username, password and app name should be the same
            assert pw_info[0][1] == info[0]
            assert pw_info[0][3:5] == info[2:4]

    # test add_password in the case where user provides no info
    def test_add_password_no_info(self, pmui_empty, monkeypatch, capsys):
        # make sure no info is returned
        monkeypatch.setattr(pm_ui.PM_UI, 'get_unique_info_from_user', lambda *args: None)

        assert pmui_empty.add_password() is None
        printed = capsys.readouterr()[0]
        assert 'Adding password canceled.' in printed
    
    # the case where user canceled password generation
    def test_add_password_no_password(self, pmui_empty, monkeypatch, capsys):
        # generate some random info = (username, app, email, url)
        info = tuple(crypto_stuff.generate_password() for _ in range(4))
        monkeypatch.setattr(pm_ui.PM_UI, 'get_unique_info_from_user', lambda *args: info)

        monkeypatch.setattr(pm_ui, 'how_to_generate_pw', lambda: 3)
        monkeypatch.setattr(pm_ui, 'generate_pw', lambda *args: '')

        pmui_empty.add_password()

        printed = capsys.readouterr()[0]

        assert 'Adding password canceled.' in printed


    def test_add_password(self, pmui_empty, monkeypatch, capsys):
        # generate some random info = (username, app, email, url)
        info = tuple(crypto_stuff.generate_password() for _ in range(4))
        monkeypatch.setattr(pm_ui.PM_UI, 'get_unique_info_from_user', lambda *args: info)

        # generate a password to go with the info
        monkeypatch.setattr(pm_ui, 'how_to_generate_pw', lambda: 3)
        pw = crypto_stuff.generate_password()
        monkeypatch.setattr(pm_ui, 'generate_pw', lambda *args: pw)

        monkeypatch.setattr(pm_ui, 'yes_or_no_question', lambda *args: 'y')

        pmui_empty.add_password() is None

        # text indicating success was printed on the screen
        printed = capsys.readouterr()[0]
        success_text = f'Password for user {info[0]} to app {info[2]} has been saved to the database.'

        assert success_text in printed

        # the password and related info was saved to db
        pw_info = pmui_empty.pm.find_password(info[2])
        # it is extremely unlikely that the previous app would show up here
        assert len(pw_info) == 1
        assert pw_info[0][1] == info[0]
        assert pw_info[0][3] == pw
        assert pw_info[0][4] == info[2]

    # what happens if user tries many times to 'generate' password
    @pytest.mark.parametrize(
        'choice, num_of_tries', [
            (1, 2),
            (1, 4),
            (2, 2),
            (2, 5)
        ]
    )
    def test_add_password_regenerate_password(self, pmui_empty, monkeypatch, capsys, choice, num_of_tries):
        # generate some random info = (username, app, email, url)
        info = tuple(crypto_stuff.generate_password() for _ in range(4))
        monkeypatch.setattr(pm_ui.PM_UI, 'get_unique_info_from_user', lambda *args: info)

        count = [0]

        monkeypatch.setattr(pm_ui, 'how_to_generate_pw', lambda: choice)
        # pw = crypto_stuff.generate_password()
        monkeypatch.setattr(pm_ui, 'generate_pw', lambda *args: crypto_stuff.generate_password())

        monkeypatch.setattr(pm_ui, 'reveal_password', lambda *args: print(f'Try {count[0]}'))

        def time_to_stop(*args):
            count[0] += 1
            if count[0] >= num_of_tries:
                return True
            return False

        monkeypatch.setattr(pm_ui.PM_UI, 'save_password_to_db_or_not', time_to_stop)

        pmui_empty.add_password()

        printed = capsys.readouterr()[0]

        assert 'Password has been generated.' in printed

        for i in range(num_of_tries):
            assert f'Try {i}' in printed



@pytest.fixture(scope='module')
def some_info():
    return [(f'user{i}', f'email{i}@d.c', f'App{i}', f'www.app{i}.com') for i in range(13)]


@pytest.fixture(scope='class')
def pmui_w_stuff(pmui_empty, some_info):
    # add some info
    infos = [(*info[:2], f'password{i}', *info[2:]) for i, info in enumerate(some_info)]
    for info in infos:
        pmui_empty.pm.force_add_password(*info)
    return pmui_empty



class TestPMUI():


    def test_get_unique_info_from_user_no_problem(self, pmui_w_stuff, monkeypatch):
        info = ('username', 'e@mail.com', 'app', 'url of app')
        monkeypatch.setattr(pm_ui, 'get_info_from_user', lambda: info)

        assert pmui_w_stuff.get_unique_info_from_user() == info
    
    def test_get_unique_info_from_user_close(self, pmui_w_stuff, monkeypatch):
        info = ('user', 'e@mail.com', 'App9', 'url of app')
        monkeypatch.setattr(pm_ui, 'get_info_from_user', lambda: info)

        assert pmui_w_stuff.get_unique_info_from_user() == info

    def test_get_unique_info_from_user_try_try_again(self, pmui_w_stuff, monkeypatch, some_info):
        count = [-1]
        info = ('username', 'e@mail.com', 'app', 'url of app')

        def get_info(*args):
            count[0] += 1
            if count[0] < len(some_info):
                return some_info[count[0]]
            return info
        monkeypatch.setattr(pm_ui, 'get_info_from_user', get_info)

        monkeypatch.setattr(pm_ui, 'yes_or_no_question', lambda *args: 'y')

        assert pmui_w_stuff.get_unique_info_from_user() == info

    def test_get_unique_info_from_user_give_up(self, pmui_w_stuff, monkeypatch, some_info):
        count = [-1]
        def get_info(*args):
            count[0] += 1
            if count[0] < len(some_info):
                return some_info[count[0]]
        
        monkeypatch.setattr(pm_ui, 'get_info_from_user', get_info)

        def answer(*args):
            if count[0] < 10:
                return 'y'
            return 'n'

        monkeypatch.setattr(pm_ui, 'yes_or_no_question', answer)

        assert pmui_w_stuff.get_unique_info_from_user() is None

    def test_get_unique_info_from_user_capitalization(self, pmui_w_stuff, monkeypatch, capsys):
        info = ('user3', 'some@other.email', 'app3', 'url_is_here')
        monkeypatch.setattr(pm_ui, 'get_info_from_user', lambda: info)

        monkeypatch.setattr(pm_ui, 'yes_or_no_question', lambda *args: 'n')

        assert pmui_w_stuff.get_unique_info_from_user() is None

        printed = capsys.readouterr()[0]
        assert 'already in database' in printed


    def test_find_app_and_username_not_found(self, pmui_w_stuff, monkeypatch, capsys):
        app = 'nonexisting app name'
        monkeypatch.setattr('builtins.input', lambda *args: app)

        assert pmui_w_stuff.find_app_and_username('some text here') is None

        printed = capsys.readouterr()[0]
        assert f'No passwords related to {app} found\n' in printed

    @pytest.mark.parametrize(
        'index', list(range(2, 12))
    )
    def test_find_app_and_username(self, pmui_w_stuff, monkeypatch, index, some_info):
        app = f'App{index}'
        monkeypatch.setattr('builtins.input', lambda *args: app)

        result = pmui_w_stuff.find_app_and_username('some text here')

        assert len(result) == 6

        info = (*some_info[index][:2], f'password{index}', *some_info[index][2:])
        assert result[1:] == info
        assert isinstance(result[0], int)
        assert result[0] > 0

    def test_find_app_and_username_many_options(self, pmui_w_stuff, monkeypatch, capsys):
        app = f'App1'
        def give_input(*args):
            if args:
                return app
            return '0'
        monkeypatch.setattr('builtins.input', give_input)

        assert pmui_w_stuff.find_app_and_username('some text here') == []

        printed = capsys.readouterr()[0]

        assert 'Search cancelled.' in printed

    @pytest.mark.parametrize(
        'choice', list(range(1, 5))
    )
    def test_find_app_and_username_choose_option(self, pmui_w_stuff, monkeypatch, choice):
        app = f'App1'
        def give_input(*args):
            if args:
                return app
            return str(choice)
        monkeypatch.setattr('builtins.input', give_input)

        result = pmui_w_stuff.find_app_and_username('some text here')
        assert result
        assert app in result[4]

    def test_find_app_and_username_not_valid(self, pmui_w_stuff, monkeypatch):
        count = [0]
        app = f'App1'
        def give_input(*args):
            if args:
                return app
            count[0] += 1
            if count[0] < 3:
                return crypto_stuff.generate_password()
            if count[0] < 5:
                return 1729
            return '1'
        monkeypatch.setattr('builtins.input', give_input)

        result = pmui_w_stuff.find_app_and_username('some text here')
        assert result
        assert app in result[4]


    def test_find_password_for_app_no_result(self, pmui_w_stuff, monkeypatch, capsys):
        monkeypatch.setattr(pm_ui.PM_UI, 'find_app_and_username', lambda *args: None)

        assert pmui_w_stuff.find_password_for_app() is None

        # nothing gets printed since find_app_and_username
        assert capsys.readouterr()[0] == ''

    def test_find_password_for_app_no_result_proper(self, pmui_w_stuff, monkeypatch, capsys):
        app = 'nonexisting app name'
        monkeypatch.setattr('builtins.input', lambda *args: app)

        assert pmui_w_stuff.find_password_for_app() is None

        expected_text = f'Write the name of the app you want password for:\nNo passwords related to {app} found\n\n'
        assert expected_text == capsys.readouterr()[0]

    @pytest.mark.parametrize(
        'index', list(range(2,10))
    )
    def test_find_password_for_app(self, pmui_w_stuff, monkeypatch, capsys, index):
        app = f'App{index}'
        monkeypatch.setattr('builtins.input', lambda *args: app)

        success_text = f'testing was a big success{crypto_stuff.generate_password()}'
        monkeypatch.setattr(pm_ui, 'obtain_password', lambda *args: print(success_text))

        assert pmui_w_stuff.find_password_for_app() is None

        assert success_text in capsys.readouterr()[0]


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