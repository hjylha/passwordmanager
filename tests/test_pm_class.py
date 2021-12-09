from pathlib import Path
import time

import pytest

import fix_imports
import dbs
from pm_class import PM, DB_auth, DB_keys, DB_password, PasswordNotFoundError


# db with only 1 row of dummy data
@pytest.fixture
def pm_temp():
    db_path = Path(__file__).parent / 'test_db_temp.db'
    for t in ('auth', 'keys', 'password'):
        dbs.initiate_db(db_path, t, 1)
    yield PM(DB_auth(db_path), DB_keys(db_path), DB_password(db_path))
    db_path.unlink()

@pytest.fixture
def pm():
    db_path = Path(__file__).parent / 'test_db_pm.db'
    return PM(DB_auth(db_path), DB_keys(db_path), DB_password(db_path))

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


def test_change_master_password(pm):
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