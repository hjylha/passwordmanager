from pathlib import Path
import string
import os

import pytest

import fix_imports
import dbs


# 'empty' db
@pytest.fixture
def db():
    db_path = Path('test_db.db')
    yield dbs.DB_general(db_path)
    db_path.unlink()

# test key db
@pytest.fixture
def dbk():
    return dbs.initiate_keys_db('test_keys.db')

# test password data db
@pytest.fixture
def dbp():
    return dbs.initiate_password_db('test_pwd.db')

class TestDummydata():

    def test_generate_dummy_string(self):
        string_type = 'normal'
        dummy_string = dbs.generate_dummy_string(string_type)
        assert isinstance(dummy_string, str)

        string_type = 'key'
        dummy_string = dbs.generate_dummy_string(string_type)
        assert isinstance(dummy_string, bytes)

        string_type = 'hash'
        dummy_string = dbs.generate_dummy_string(string_type)
        assert isinstance(dummy_string, str)
        dummy_list = dummy_string.split('$')
        assert len(dummy_list) == 6
        assert dummy_list[0] == ''
        assert dummy_list[1] == 'argon2id'

        # how about with given encryptor or hasher?
        f = dbs.cs.do_crypto_stuff('password', os.urandom(16), 5)
        ph = dbs.cs.PasswordHasher()

        string_type = 'normal'
        dummy_string = dbs.generate_dummy_string(string_type, f)
        assert isinstance(dummy_string, str)

        string_type = 'key'
        dummy_string = dbs.generate_dummy_string(string_type, f)
        assert isinstance(dummy_string, bytes)

        string_type = 'hash'
        dummy_string = dbs.generate_dummy_string(string_type, password_hasher=ph)
        assert isinstance(dummy_string, str)
        dummy_list = dummy_string.split('$')
        assert len(dummy_list) == 6
        assert dummy_list[0] == ''
        assert dummy_list[1] == 'argon2id'

    def test_generate_dummy_data(self):
        num = 5
        f = dbs.cs.do_crypto_stuff('password', os.urandom(16), 5)
        ph = dbs.cs.PasswordHasher()
        dummy_data = dbs.generate_dummy_data(('hash', 'key', 'normal'), num, f, ph)
        assert len(dummy_data) == num
        assert dummy_data[2][0].split('$')[1] == 'argon2id'


class TestInitiation():

    def test_initiate_auth_db(self, db):
        dba = dbs.initiate_db(db.filepath, 'auth')
        assert len(dba.select_all('auth')) == 10

    def test_initiate_keys_db(self, db):
        dbk = dbs.initiate_db(db.filepath, 'keys')
        assert len(dbk.select_all('app_keys')) == 10
        assert len(dbk.select_all('email_keys')) == 10
        assert len(dbk.select_all('data_keys')) == 10


    def test_initiate_password_db(self, db):
        dbp = dbs.initiate_db(db.filepath, 'password')
        assert len(dbp.select_all('apps')) == 10
        assert len(dbp.select_all('emails')) == 10
        assert len(dbp.select_all('data')) == 10