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

# some rowids and keys
@pytest.fixture
def rows_and_keys():
    return {1: b'LCXUP0NV1rBDawSLHy9soxhYA8Mo5dBR1-icCsMrq_Q=',
            3: b'u6ztSn24XJDRQNZlEZdLJ2bpQeXuCq2vtanG-cjZvuc=',
            6: b'7j0pRSoSV1AeDpddhNX9FdHuVWQtK5QkXHpnE7ePj3o='}

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
        table = 'app_keys'
        vacancies = dbk.find_vacancies(table, master_key)
        # added keys to rowids 2 and 5
        assert vacancies[1] == [2, 5]
        assert vacancies[0] == [i+1 for i in range(10) if i+1 not in [2, 5]]

        table = 'email_keys'
        vacancies = dbk.find_vacancies(table, master_key)
        assert vacancies[1] == []
        assert vacancies[0] == [i+1 for i in range(10)]
                
    
    def test_insert_key(self, dbk, master_key):
        key = dbs.Fernet.generate_key()
        table = dbk.table_tuple[0]  # 'app_keys'
        rowid = 5
        # before
        row_before = dbk.select_row_by_rowid(table, rowid)
        dbk.insert_key(key, table, rowid, master_key)
        # after
        row_after = dbk.select_row_by_rowid(table, rowid)
        assert row_after != row_before
        # check the key and in_use
        f = dbs.Fernet(master_key)
        assert key == f.decrypt(row_after[1])
        assert 'in_use' == f.decrypt(row_after[2].encode()).decode()

    def test_add_new_key(self, dbk, master_key):
        table = 'data_keys'
        # before
        rows_before = dbk.select_all(table)
        rowid, key = dbk.add_new_key(table, master_key)

        row_after = dbk.select_row_by_rowid(table, rowid)
        assert rows_before[rowid-1] != row_after
        # check the key and in_use
        f = dbs.Fernet(master_key)
        assert key == f.decrypt(row_after[1])
        assert 'in_use' == f.decrypt(row_after[2].encode()).decode()

    def test_decrypt_key(self, dbk, master_key):
        key = dbs.Fernet.generate_key()
        f = dbs.Fernet(master_key)
        enc_key = f.encrypt(key)
        assert key == dbk.decrypt_key(enc_key, master_key)
    
    def test_get_rows_and_keys(self, dbk, master_key):
        table = 'app_keys'

        # add one more
        rowid = 2
        key = b'QJp3y4CS5gPKIQIrZg1m3IzshLMGIamvoaPj9rvSctU='
        dbk.insert_key(key, table, rowid, master_key)

        rows_and_keys = dbk.get_rows_and_keys(table, master_key)
        assert list(rows_and_keys.keys()) == [2, 5]
        keys = list(rows_and_keys.values())
        assert keys[0] == key
        assert isinstance(keys[1], bytes)



class TestDBpassword():
    
    def test_insert_data(self, dbp, rows_and_keys):
        for rowid, key in rows_and_keys.items():
            row_and_key = (rowid, key)
            data = ['important data here', 'something']
            # to check
            f = dbs.Fernet(key)
            # wrong data_type raises an exception
            data_type = 'nonsense'
            with pytest.raises(Exception):
                dbp.insert_data(data_type, data, row_and_key)

            row_before = dbp.select_row_by_rowid('apps', rowid)
            data_type = 0
            data = [f'app{rowid}', f'0000{rowid}']
            dbp.insert_data(data_type, data, row_and_key)
            row_after = dbp.select_row_by_rowid('apps', rowid)
            assert row_before != row_after
            for i, item in enumerate(data):
                assert f.decrypt(row_after[i+1].encode()).decode() == item
            # no errors with timestamp
            int(f.decrypt(row_after[-1].encode()).decode())
            
            row_before = dbp.select_row_by_rowid('emails', rowid)
            data_type = 1
            data = [f'mail{rowid}@email.com', f'0000{rowid}']
            dbp.insert_data(data_type, data, row_and_key)
            row_after = dbp.select_row_by_rowid('emails', rowid)
            assert row_before != row_after
            for i, item in enumerate(data):
                assert f.decrypt(row_after[i+1].encode()).decode() == item
            # no errors with timestamp
            int(f.decrypt(row_after[-1].encode()).decode())

            row_before = dbp.select_row_by_rowid('data', rowid)
            data_type = 2
            data = ['username', '00001', 'password', '0000003', 'url']
            dbp.insert_data(data_type, data, row_and_key)
            row_after = dbp.select_row_by_rowid('data', rowid)
            assert row_before != row_after
            for i, item in enumerate(data):
                assert f.decrypt(row_after[i+1].encode()).decode() == item
            # no errors with timestamp
            int(f.decrypt(row_after[-1].encode()).decode())

    def test_get_list(self, dbp, rows_and_keys):
        app_list = dbp.get_list(0, rows_and_keys)
        assert app_list == ['app1', 'app3', 'app6']

        app_list = dbp.get_list(1, rows_and_keys)
        assert app_list == ['mail1@email.com', 'mail3@email.com', 'mail6@email.com']

    def test_find(self, dbp, rows_and_keys):
        search_text = 'app'
        results = dbp.find(0, search_text, rows_and_keys)
        assert results == [(1, 'app1'), (3, 'app3'), (6, 'app6')]

        search_text = '1'
        results = dbp.find(0, search_text, rows_and_keys)
        assert results == [(1, 'app1')]

        search_text = 'mail3'
        results = dbp.find(1, search_text, rows_and_keys)
        assert results == [(3, 'mail3@email.com')]

        search_text = 'nonsense'
        results = dbp.find(1, search_text, rows_and_keys)
        assert results == []