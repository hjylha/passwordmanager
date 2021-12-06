from pathlib import Path
import string
import os
from cryptography.fernet import Fernet

import pytest

import fix_imports
import dbs
from dbs import DB_auth, DB_keys, DB_password


# master key
@pytest.fixture
def master_key():
    return b'GJbXfxE9MjLNcVUlP3uYm3qziEJY6IJARBbWsu1Y8ac='

# 'empty' db
@pytest.fixture
def db():
    db_path = Path('test_db.db')
    yield dbs.DB_general(db_path)
    db_path.unlink()

# test auth db
@pytest.fixture
def dba():
    return DB_auth('test_db_auth.db')

# test key db
@pytest.fixture
def dbk():
    return DB_keys('test_db_keys.db')

# test password data db
@pytest.fixture
def dbp():
    return DB_password('test_db_pwd.db')


class TestDummydata():

    def test_generate_dummy_string(self):
        string_type = 'normal'
        dummy_string = dbs.generate_dummy_string(string_type)
        assert isinstance(dummy_string, str)

        string_type = 'key'
        dummy_string = dbs.generate_dummy_string(string_type)
        assert isinstance(dummy_string, bytes)
        # f = Fernet(Fernet.generate_key())
        # f.decrypt(dummy_string)

        string_type = 'hash'
        dummy_string = dbs.generate_dummy_string(string_type)
        assert isinstance(dummy_string, str)
        dummy_list = dummy_string.split('$')
        assert len(dummy_list) == 6
        assert dummy_list[0] == ''
        assert dummy_list[1] == 'argon2id'

        string_type = 'not a type'
        with pytest.raises(Exception):
            dbs.generate_dummy_string(string_type)

        # how about with given encryptor or hasher?
        f = dbs.cs.do_crypto_stuff('password', os.urandom(16), 5)
        ph = dbs.cs.PasswordHasher()

        string_type = 'normal'
        dummy_string = dbs.generate_dummy_string(string_type, f)
        assert isinstance(dummy_string, str)

        string_type = 'key'
        dummy_string = dbs.generate_dummy_string(string_type, f)
        assert isinstance(dummy_string, bytes)
        # try to deccrypt with the same f should not be a problem
        f.decrypt(dummy_string)

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
    
    def test_initiate_db_fail(self, db):
        with pytest.raises(Exception):
            dbs.initiate_db(db.filepath, 'not a type')

class TestDBauth():

    def test_is_key_in_keys(self, dba):
        key = dbs.Fernet.generate_key()
        e_key = dbs.Fernet(key).encrypt(key)
        # it is extremely unlikely that e_key is among keys
        assert not dba.is_key_in_keys(e_key)

        # this should be in keys
        e_key = b'gAAAAABhrgu_1yd1dxYsD7DNk36vqwbmzwF6zAaBMbbD2Oyh5NDGGPUBvZ37fOQjH_ZhfOLGV-tTUkbNSj2wKBsjdKbctheo1UeiGvFDLRdN7yFrRs_rre08WU4XF0Pky76ZZ8OkN6b_'
        assert dba.is_key_in_keys(e_key)

    def test_check_uniqueness_of_keys(self, dba):
        # it is extremely unlikely that there would be two same encrypted keys
        assert dba.check_uniqueness_of_keys()

    # test add and check password
    def test_add_password(self, dba):
        data0 = dba.select_all(dba.table)
        password = dbs.cs.generate_password()
        salt = b'SBHe5zI8OkN94rsVHSZE3dwAvimz-ukl11ONcJgEAbo='
        dba.add_password(password, salt)

        # something should have changed
        data = dba.select_all(dba.table)
        assert any(row0 != row for row0, row in zip(data0, data))

        # this key should be in keys
        e_key = dba.check_password(password)
        assert dba.is_key_in_keys(e_key)

    # def test_check_password(self, dba):
    #     password = 'g00d p4ssw0rd'
    #     salt = b'SBHe5zI8OkN94rsVHSZE3dwAvimz-ukl11ONcJgEAbo='
    #     dba.add_password(password, salt)

    def test_decrypt_key(self, dba):
        password = 'g00d p4ssw0rd'
        salt = b'SBHe5zI8OkN94rsVHSZE3dwAvimz-ukl11ONcJgEAbo='
        rowid = 5
        f = dbs.cs.do_crypto_stuff(password, salt, 200_000)
        key = dbs.Fernet.generate_key()
        encrypted_key = f.encrypt(key)
        dba.update_by_rowid(dba.table, (dba.cols[1],), (encrypted_key,), rowid)

        # check that we can decrypt the key
        row = dba.select_row_by_rowid(dba.table, rowid)
        # assert row[2] == encrypted_key
        assert dba.decrypt_key(row[2], password, salt) == key


class TestDBkeys():

    def test_find_vacancies(self, dbk, master_key):
        for table in dbk.table_tuple:
            vacancies = dbk.find_vacancies(table, master_key)
            assert vacancies[1] == []
            assert vacancies[0] == [i+1 for i in range(10)]
    
    def test_insert_key(self, dbk, master_key):
        pass

    def test_add_new_key(self, dbk, master_key):
        pass

    def test_decrypt_key(self, master_key):
        pass



class TestDBpassword():
    pass
