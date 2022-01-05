import os
from pathlib import Path
import time

import pytest

import fix_imports
import dbs
from dbs import DB_auth, DB_keys, DB_password
from pm_class import PM, is_valid_email, is_valid_url


@pytest.fixture
def default_salt():
    return b'\xc1\x95\xe15=\tm\xef\xecTH\x8e\xf5;/l'

# some test inserts
@pytest.fixture
def password_info_lines():
    return [(f'user{i}', f'email{i}@provider.com', f'pwd{i}', f'app{i}', f'app{i}.net') for i in range(20)]


# db with only 1 row of dummy data
@pytest.fixture
def pm_temp():
    db_path = Path(__file__).parent / 'test_db_temp.db'
    for t in ('auth', 'keys', 'password'):
        dbs.initiate_db(db_path, t, 1)
    yield PM(os.urandom(16), DB_auth(db_path), DB_keys(db_path), DB_password(db_path))
    db_path.unlink()

# "proper" db
@pytest.fixture
def pm(default_salt):
    db_path = Path(__file__).parent / 'test_db_pm.db'
    if not db_path.exists():
        for t in ('auth', 'keys', 'password'):
            dbs.initiate_db(db_path, t)
    return PM(default_salt, DB_auth(db_path), DB_keys(db_path), DB_password(db_path))

# db with master_key "active"
@pytest.fixture
def pm_w_master_key(pm):
    master_password = '0K_p455w0rd'
    if not pm.check_master_password(master_password):
        pm.add_master_password(master_password)
    return pm

# db with other stuff as well
@pytest.fixture
def pm_w_stuff(pm_w_master_key):
    pm_w_master_key.set_name_lists()
    return pm_w_master_key


# onto the testing
# first fcns checking validity of email and url
class TestValidators():
    @pytest.mark.parametrize(
        'email, is_valid', [
            ('text@__fdfdfadfsadfa.lkjasdf', True),
            ('big space@server.com', False),
            ('no_at_sign_but.con', False),
            ('too_many_@_signs_@q.w', False),
            ('one.but@not_on_the_right_side', False)]
    )
    def test_is_valid_email(self, email, is_valid):
        assert is_valid_email(email) == is_valid


    @pytest.mark.parametrize(
        'url, is_valid', [
            ('place.after_dot', True),
            ('big space.com', False),
            ('something_is_missing', False)
        ]
    )
    def test_is_valid_url(self, url, is_valid):
        assert is_valid_url(url) == is_valid



def test_init(pm):
    # check some methods of different classes
    assert pm.dba.check_uniqueness_of_keys()
    # pm.dbk

class TestwTempDB():
    def test_add_master_password(self, pm_temp):
        password = 'pw is good'
        pm_temp.add_master_password(password)
        # check what happened to the one row
        row = pm_temp.dba.select_all(pm_temp.dba.table)[0]
        # check password
        ph = dbs.cs.PasswordHasher()
        assert ph.verify(row[1], password)
        # check encryption
        f = dbs.cs.do_crypto_stuff(password, pm_temp.salt, 200_000)
        assert pm_temp.master_key == f.decrypt(row[2])
        # hashing takes time, but not more than 2 seconds
        time_in_db = int(dbs.cs.decrypt_text(row[3], f))
        assert int(time.time()) - time_in_db < 3


    def test_check_master_password(self, pm_temp):
        password = 'not gonna be found'
        assert not pm_temp.check_master_password(password)
        
        password = 'test_password'
        pm_temp.add_master_password(password)
        assert pm_temp.check_master_password(password)
    
    def test_master_key_fail(self, pm_temp):
        with pytest.raises(Exception):
            pm_temp.find_info(0, 'whatever')
        with pytest.raises(Exception):
            pm_temp.find_info(1, 'whatever')
        with pytest.raises(Exception):
            pm_temp.add_info(0, 'whatever')
        with pytest.raises(Exception):
            pm_temp.add_info(1, 'whatever')

class TestChangePassword():
    def test_change_master_password(self, pm):
        # pw = 'original pw'
        pw = dbs.cs.generate_password()
        pm.add_master_password(pw)

        # going deep to check things
        rowid, e_key = pm.dba.check_password(pw, True)
        row = pm.dba.select_row_by_rowid(pm.dba.table, rowid)
        ph = dbs.cs.PasswordHasher()
        assert ph.verify(row[1], pw)
        assert row[2] == e_key
        master_key = pm.dba.decrypt_key(e_key, pw, pm.salt)
        assert master_key == pm.master_key

        # new_pw = 'new pw'
        new_pw = dbs.cs.generate_password()
        pm.change_master_password(pw, new_pw, False)
        assert master_key == pm.master_key
        row = pm.dba.select_row_by_rowid(pm.dba.table, rowid)
        assert ph.verify(row[1], new_pw)
        assert master_key == pm.dba.decrypt_key(row[2], new_pw, pm.salt)

        newer_pw = dbs.cs.generate_password()
        pm.change_master_password(new_pw, newer_pw)
        assert master_key != pm.master_key
        row = pm.dba.select_row_by_rowid(pm.dba.table, rowid)
        assert ph.verify(row[1], newer_pw)
        assert pm.master_key == pm.dba.decrypt_key(row[2], newer_pw, pm.salt)

    
class TestPasswordManagement():

    def test_set_name_lists(self, pm_w_master_key):
        pm_w_master_key.set_name_lists()
        assert isinstance(pm_w_master_key.app_list, list)
        assert isinstance(pm_w_master_key.email_list, list)
    
    def test_add_info(self, pm_w_stuff):
        app = 'good app'
        rowid = pm_w_stuff.add_info(0, app)
        info = pm_w_stuff.find_info(0, app)
        assert len(info) == 1
        assert info[0] == (rowid, app)
        # assert app in [a for _, a in info]
        assert app in [a for _, a in pm_w_stuff.app_list]

        email = 'zoomin@place.org'
        rowid = pm_w_stuff.add_info(1, email)
        info = pm_w_stuff.find_info(1, email)
        assert len(info) == 1
        assert info[0] == (rowid, email)
        # assert email in [a for _, a in info]
        assert email in [a for _, a in pm_w_stuff.email_list]

        # not valid email should be saved as -
        email = 'not a valid email'
        rowid = pm_w_stuff.add_info(1, email)
        info = pm_w_stuff.find_info(1, email)
        assert not info
        info = pm_w_stuff.find_info(1, '-')
        assert info
        assert '-' in [a for _, a in pm_w_stuff.email_list]

    def test_find_info(self, pm_w_master_key):
        app = 'not here'
        assert pm_w_master_key.find_info(0, app) == []
        assert pm_w_master_key.find_info(1, app) == []
        # this should have been added
        app = 'good app'
        assert pm_w_master_key.find_info(0, app)[0][1] == app  

    def test_prepare_to_add_password(self, pm_w_master_key):
        app = 'good app'
        email = 'zoomin@place.org'
        infos = pm_w_master_key.prepare_to_add_password(app, email)
        assert len(infos[app]) == 1
        assert len(infos[email]) == 1

    def test_add_password(self, pm_w_stuff):
        app = 'good app'
        email = 'zoomin@place.org'
        username = 'user001'
        password = 'no effort'
        url = 'goodapp.com'
        infos = pm_w_stuff.prepare_to_add_password(app, email)
        a = infos[app][0][0]
        e = infos[email][0][0]
        added = pm_w_stuff.add_password(username, e, password, a, url)
        # see if the info can be found
        pw_infos = pm_w_stuff.find_password(app)
        if added:
            assert isinstance(pw_infos[0][0], int)
        else:
            assert len(pw_infos) == 1
        assert pw_infos[0][1:] == (username, email, password, app, url)

        # make a different search
        pw_infos = pm_w_stuff.find_password('a', False, username)
        assert len(pw_infos) == 1
        assert pw_infos[0][1] == username
        assert pw_infos[0][2] == email
        assert pw_infos[0][3] == password
        assert pw_infos[0][4] == app
        assert pw_infos[0][5] == url

    # def test_find_password(self, pm_w_master_key):
    #     pass

    def test_force_add_password(self, pm_w_stuff):
        username = 'big brain user'
        email = 'bbu@provider.org'
        password = '123456789'
        app = 'secret program'
        url = 'very secret'
        pm_w_stuff.force_add_password(username, email, password, app, url)

        pw_infos = pm_w_stuff.find_password(app)
        assert len(pw_infos) == 1
        # print(pw_infos[0][0])
        assert pw_infos[0][1] == username
        assert pw_infos[0][2] == email
        assert pw_infos[0][3] == password
        assert pw_infos[0][4] == app
        assert pw_infos[0][5] == url
    
    def test_force_add_password_many(self, pm_w_stuff, password_info_lines):
        for line in password_info_lines:
            pm_w_stuff.force_add_password(*line)
        
        line_num = 13
        pw_infos = pm_w_stuff.find_password(password_info_lines[line_num][3])
        assert len(pw_infos) == 1
        for i in range(5):
            assert pw_infos[0][i+1] == password_info_lines[line_num][i]
        

    def test_change_password(self, pm_w_stuff):
        app = 'good app'
        pw_infos = pm_w_stuff.find_password(app)
        rowids = tuple(row[0] for row in pw_infos)
        if not len(rowids) == 1:
            raise Exception('too many inserts...')
        rowid = rowids[0]
        new_password = 'more effort'
        pm_w_stuff.change_password(rowid, new_password)
        # checking
        assert pm_w_stuff.find_password(app)[0][3] == new_password
    
    # try to remember which apps and email have been added here
    def test_get_name_list(self, pm_w_stuff):
        app = 'another one'
        pm_w_stuff.add_info(0, app)
        # this makes it two apps, actually 3
        assert len(pm_w_stuff.get_name_list(0)) == 23
        # changed email makes it 4
        assert len(pm_w_stuff.get_name_list(1)) == 23

    def test_update_password_data(self, pm_w_stuff):
        app = 'secret program'
        email = 'user@other-provider.com'
        url = 'not-so-secret-anymore.com'
        new_data = {'email': email, 'url': url}
        rowid = pm_w_stuff.find_password(app)[0][0]
        pm_w_stuff.update_password_data(rowid, new_data)

        pw_info = pm_w_stuff.find_password(app)[0]
        assert pw_info[1] == 'big brain user'
        assert pw_info[2] == email
        assert pw_info[5] == url

        # delete this afterwards
        pm_w_stuff.delete_password(rowid)

    def test_delete_password(self, pm_w_stuff):
        app = 'good app'
        pw_infos = pm_w_stuff.find_password(app)
        rowids = tuple(row[0] for row in pw_infos)
        # remove all passwords related to app
        for r in rowids:
            pm_w_stuff.delete_password(r)
        assert pm_w_stuff.find_password(app) == []
        
        # and the same for other app
        app = 'secret program'
        pw_infos = pm_w_stuff.find_password(app)
        rowids = tuple(row[0] for row in pw_infos)
        for r in rowids:
            pm_w_stuff.delete_password(r)
        assert pm_w_stuff.find_password(app) == []

        # remove test db
        pm_w_stuff.dba.filepath.unlink()
