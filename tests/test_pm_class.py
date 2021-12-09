from pathlib import Path
import time

import pytest

import fix_imports
import dbs
from pm_class import PM, DB_auth, DB_keys, DB_password, PasswordNotFoundError


# get some dummy app names and email addresses
@pytest.fixture
def app_list():
    return [f'app{i}' for i in range(100)]

@pytest.fixture
def email_list():
    return [f'email{i}@provider.com' for i in range(100)]


# db with only 1 row of dummy data
@pytest.fixture
def pm_temp():
    db_path = Path(__file__).parent / 'test_db_temp.db'
    for t in ('auth', 'keys', 'password'):
        dbs.initiate_db(db_path, t, 1)
    yield PM(DB_auth(db_path), DB_keys(db_path), DB_password(db_path))
    db_path.unlink()

# "proper" db
@pytest.fixture
def pm():
    db_path = Path(__file__).parent / 'test_db_pm.db'
    return PM(DB_auth(db_path), DB_keys(db_path), DB_password(db_path))

# db with master_key "active"
@pytest.fixture
def pm_w_master_key(pm):
    master_password = '0K_p455w0rd'
    if not pm.check_master_password(master_password):
        pm.add_master_password(master_password)
    return pm


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
        f = dbs.cs.do_crypto_stuff(password, pm_temp.get_salt(), 200_000)
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
        master_key = pm.dba.decrypt_key(e_key, pw, pm.get_salt())
        assert master_key == pm.master_key

        # new_pw = 'new pw'
        new_pw = dbs.cs.generate_password()
        pm.change_master_password(pw, new_pw, False)
        assert master_key == pm.master_key
        row = pm.dba.select_row_by_rowid(pm.dba.table, rowid)
        assert ph.verify(row[1], new_pw)
        assert master_key == pm.dba.decrypt_key(row[2], new_pw, pm.get_salt())

        newer_pw = dbs.cs.generate_password()
        pm.change_master_password(new_pw, newer_pw)
        assert master_key != pm.master_key
        row = pm.dba.select_row_by_rowid(pm.dba.table, rowid)
        assert ph.verify(row[1], newer_pw)
        assert pm.master_key == pm.dba.decrypt_key(row[2], newer_pw, pm.get_salt())

    
class TestPasswordManagement():
    
    def test_add_info(self, pm_w_master_key):
        app = 'good app'
        pm_w_master_key.add_info(0, app)
        info = pm_w_master_key.find_info(0, app)
        assert len(info) == 1
        assert app in [a for _, a in info]

        email = 'zoomin@place.org'
        pm_w_master_key.add_info(1, email)
        info = pm_w_master_key.find_info(1, email)
        assert len(info) == 1
        assert email in [a for _, a in info]

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

    def test_add_password(self, pm_w_master_key):
        app = 'good app'
        email = 'zoomin@place.org'
        username = 'user001'
        password = 'no effort'
        url = 'goodapp.com'
        infos = pm_w_master_key.prepare_to_add_password(app, email)
        a = infos[app][0][0]
        e = infos[email][0][0]
        pm_w_master_key.add_password(username, e, password, a, url)
        # see if the info can be found
        pw_infos = pm_w_master_key.find_password(app)
        assert pw_infos[0][1] == username
        assert pw_infos[0][2] == e
        assert pw_infos[0][3] == password
        assert pw_infos[0][4] == a
        assert pw_infos[0][5] == url

    # def test_find_password(self, pm_w_master_key):
    #     pass
        

    def test_change_password(self, pm_w_master_key):
        app = 'good app'
        pw_infos = pm_w_master_key.find_password(app)
        rowids = tuple(row[0] for row in pw_infos)
        if not len(rowids) == 1:
            raise Exception('too many inserts...')
        rowid = rowids[0]
        new_password = 'more effort'
        pm_w_master_key.change_password(rowid, new_password)
        # checking
        assert pm_w_master_key.find_password(app)[0][3] == new_password


    def test_delete_password(self, pm_w_master_key):
        app = 'good app'
        pw_infos = pm_w_master_key.find_password(app)
        rowids = tuple(row[0] for row in pw_infos)
        # remove all passwords related to app
        for r in rowids:
            pm_w_master_key.delete_password(r)
        assert pm_w_master_key.find_password(app) == []
