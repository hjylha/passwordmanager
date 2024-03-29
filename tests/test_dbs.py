from pathlib import Path
import string
import os
import sqlite3
import time

# from cryptography.fernet import Fernet
import pytest

import fix_imports
import dbs
from dbs import DB_auth, DB_keys, DB_password


# salt
@pytest.fixture(scope='module')
def salt():
    return dbs.Fernet.generate_key()
    # return b'SBHe5zI8OkN94rsVHSZE3dwAvimz-ukl11ONcJgEAbo='

# master key
@pytest.fixture(scope='module')
def master_key():
    return dbs.Fernet.generate_key()
    # return b'GJbXfxE9MjLNcVUlP3uYm3qziEJY6IJARBbWsu1Y8ac='

# some rowids and keys
@pytest.fixture(scope='module')
def rows_and_keys():
    return {1: dbs.Fernet.generate_key(),
            3: dbs.Fernet.generate_key(),
            6: dbs.Fernet.generate_key()}
    # return {1: b'LCXUP0NV1rBDawSLHy9soxhYA8Mo5dBR1-icCsMrq_Q=',
            # 3: b'u6ztSn24XJDRQNZlEZdLJ2bpQeXuCq2vtanG-cjZvuc=',
            # 6: b'7j0pRSoSV1AeDpddhNX9FdHuVWQtK5QkXHpnE7ePj3o='}

# 'empty' db
@pytest.fixture
def db():
    db_path = Path(__file__).parent / 'test_db.db'
    yield dbs.DB_general(db_path)
    db_path.unlink()

# test auth db
@pytest.fixture(scope='class')
def dba():
    db_path = Path(__file__).parent / 'test_db_auth.db'
    if not db_path.exists():
        dbs.initiate_db(db_path, 'auth')
    yield DB_auth(db_path)
    db_path.unlink()

# test key db
@pytest.fixture(scope='class')
def dbk():
    db_path = Path(__file__).parent / 'test_db_keys.db'
    if not db_path.exists():
        dbs.initiate_db(db_path, 'keys')
    yield DB_keys(db_path)
    db_path.unlink()

# test password data db
@pytest.fixture(scope='class')
def dbp():
    db_path = Path(__file__).parent / 'test_db_pwd.db'
    if not db_path.exists():
        dbs.initiate_db(db_path, 'password')
    yield DB_password(db_path)
    db_path.unlink()


class TestSearch():
    def test_find_from_list(self):
        word = 'EmAiL'
        app_list = [(1, 'ma1l1@email.com'), (3, 'ma1l3@email.com'), (6, 'mail6@email.com')]
        assert app_list == dbs.find_from_list(word, app_list)
        assert dbs.find_from_list(word, app_list, True) == []

        word = 'MA1L'
        assert dbs.find_from_list(word, app_list) == [(1, 'ma1l1@email.com'), (3, 'ma1l3@email.com')]

        word = 'ma1l3@email.com'
        assert dbs.find_from_list(word, app_list, True) == [(3, 'ma1l3@email.com')]


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

    def test_initiate_filepath(self):
        path = Path.cwd() / 'more_tests' / 'testing.db'
        dba = dbs.initiate_db(path, 'auth')
        assert len(dba.select_all('auth')) == 10
        path.unlink()
        path.parent.rmdir()

    @pytest.mark.parametrize(
        'num_of_dummies', [
            0, 1, 10, 20
        ]
    )
    def test_initiate_auth_db(self, db, num_of_dummies):
        dba = dbs.initiate_db(db.filepath, 'auth', num_of_dummies)
        assert len(dba.select_all('auth')) == num_of_dummies

    @pytest.mark.parametrize(
        'num_of_dummies', [
            0, 1, 10, 20
        ]
    )
    def test_initiate_keys_db(self, db, num_of_dummies):
        dbk = dbs.initiate_db(db.filepath, 'keys', num_of_dummies)
        assert len(dbk.select_all('app_keys')) == num_of_dummies
        assert len(dbk.select_all('email_keys')) == num_of_dummies
        assert len(dbk.select_all('data_keys')) == num_of_dummies

    @pytest.mark.parametrize(
        'num_of_dummies', [
            0, 1, 10, 20
        ]
    )
    def test_initiate_password_db(self, db, num_of_dummies):
        dbp = dbs.initiate_db(db.filepath, 'password', num_of_dummies)
        assert len(dbp.select_all('apps')) == num_of_dummies
        assert len(dbp.select_all('emails')) == num_of_dummies
        assert len(dbp.select_all('data')) == num_of_dummies
    
    def test_initiate_db_fail(self, db):
        with pytest.raises(Exception):
            dbs.initiate_db(db.filepath, 'not a type')
    
    def test_init_DB_auth(self, db):
        with pytest.raises(Exception):
            DB_auth(db.filepath, 0)
        
        dbs.initiate_db(db.filepath, 'auth', 1)
        dba = DB_auth(db.filepath, 1)
        assert len(dba.select_all('auth')) == 1

    def test_init_DB_keys(self, db):
        with pytest.raises(Exception):
            DB_keys(db.filepath, 0)
        
        dbs.initiate_db(db.filepath, 'keys', 1)
        dbk = DB_keys(db.filepath, 1)
        assert len(dbk.select_all('app_keys')) == 1
        assert len(dbk.select_all('email_keys')) == 1
        assert len(dbk.select_all('data_keys')) == 1
    
    def test_init_DB_pwd(self, db):
        with pytest.raises(Exception):
            DB_password(db.filepath, 0)
        
        dbs.initiate_db(db.filepath, 'password', 1)
        dbp = DB_password(db.filepath, 1)
        assert len(dbp.select_all('apps')) == 1
        assert len(dbp.select_all('emails')) == 1
        assert len(dbp.select_all('data')) == 1


class TestDBauth():

    def test_is_key_in_keys(self, dba):
        key = dbs.Fernet.generate_key()
        e_key = dbs.Fernet(key).encrypt(key)
        # it is extremely unlikely that e_key is among keys
        assert not dba.is_key_in_keys(e_key)

        # see what is in master key column
        conn = sqlite3.connect(Path(__file__).parent / 'test_db_auth.db')
        cur = conn.cursor()
        cur.execute('SELECT master_key FROM auth')
        keys = cur.fetchall()
        # they are all in keys
        for key in keys:
            assert dba.is_key_in_keys(key[0])

    def test_check_uniqueness_of_keys(self, dba):
        # it is extremely unlikely that there would be two same encrypted keys
        assert dba.check_uniqueness_of_keys()
    
    # this doesn't really have much to do with db
    def test_decrypt_key(self, dba):
        password = dbs.cs.generate_password()
        # salt = b'SBHe5zI8OkN94rsVHSZE3dwAvimz-ukl11ONcJgEAbo='
        salt = os.urandom(16)
        f = dbs.cs.do_crypto_stuff(password, salt, 200_000)
        key = dbs.Fernet.generate_key()
        encrypted_key = f.encrypt(key)
        assert dba.decrypt_key(encrypted_key, password, salt) == key

    # testing add and check password are connected
    def test_add_password(self, dba, salt):
        data0 = dba.select_all(dba.table)
        password = 'testing'
        key = b'SlLYcsRiBK2mR0LbuX6oUy_CbHXnkmo-xbtSwY7Po68='
        rowid = 2
        master_key = dba.add_password(password, salt, key, rowid)
        # rowids stayed the same, but otherwise things changed
        row2 = dba.select_row_by_rowid(dba.table, rowid)
        assert row2[0] == data0[1][0]
        assert all(item != item0 for item, item0 in zip(row2[1:], data0[1][1:]))
        # maybe we can decrypt things
        assert master_key == key
        assert dba.decrypt_key(row2[2], password, salt) == key
        # this should be quite quick 
        time_in_db = dba.decrypt_key(row2[3].encode(), password, salt).decode()
        assert int(time.time()) - int(time_in_db) < 2
        # also check check_password here as well
        assert row2[2] == dba.check_password(password)
        assert (rowid, row2[2]) == dba.check_password(password, True)

        # it is extremely unlikely that generated password is already in db
        password = dbs.cs.generate_password()
        # password = 'g00d p4ssw0rd'
        dba.add_password(password, salt)
        # this key should be in keys
        e_key = dba.check_password(password)
        assert dba.is_key_in_keys(e_key)

    def test_check_password(self, dba, salt):
        password = dbs.cs.generate_password()
        # salt = b'SBHe5zI8OkN94rsVHSZE3dwAvimz-ukl11ONcJgEAbo='
        key = b'f5djulfNmLjh8_Jdrj40_u_2dA-U_tjyWOb90ThyHOI='
        dba.add_password(password, salt, key)
        encrypted_key = dba.check_password(password)
        assert dba.decrypt_key(encrypted_key, password, salt) == key

        # add this password twice to get error
        password = 'g00d p4ssw0rd'
        # make sure they are not added to the same row
        row1 = dbs.cs.secrets.randbelow(dba.length) + 1
        row2 = dbs.cs.secrets.choice([i + 1 for i in range(dba.length) if i+1 != row1])
        dba.add_password(password, salt, rowid=row1)
        dba.add_password(password, salt, rowid=row2)
        with pytest.raises(Exception):
            dba.check_password(password)

        password = 'not here'
        with pytest.raises(dbs.PasswordNotFoundError):
            dba.check_password(password)


class TestDBkeys():

    def test_reset_db_keys(self, dbk):
        # should this check
        if len(dbk.select_all(dbk.table_tuple[2])) > 100:
            dbk.filepath.unlink()
            dbs.initiate_db(dbk.filepath, 'keys')
            assert len(dbk.select_all(dbk.table_tuple[0])) == 10

    def test_add_dummy_data(self, dbk):
        num_before = len(dbk.select_all('email_keys'))
        dbk.add_dummy_data(1, 1)
        num_after = len(dbk.select_all('email_keys'))
        assert num_after == num_before + 1
                
    
    def test_insert_key(self, dbk, master_key):
        key = dbs.Fernet.generate_key()
        table_num = 0  # 'app_keys'
        table = dbk.table_tuple[table_num]
        rowid = 5
        # before
        row_before = dbk.select_row_by_rowid(table, rowid)
        dbk.insert_key(key, table_num, rowid, master_key)
        # after
        row_after = dbk.select_row_by_rowid(table, rowid)
        assert row_after != row_before
        # check the key and in_use
        f = dbs.Fernet(master_key)
        assert key == f.decrypt(row_after[1])
        assert 'in_use' == f.decrypt(row_after[2].encode()).decode()

    def test_add_new_key(self, dbk, master_key):
        # table = 'data_keys'
        table_num = 2  # 'app_keys'
        table = dbk.table_tuple[table_num]
        # before
        rows_before = dbk.select_all(table)
        rowid, key = dbk.add_new_key(table_num, master_key)

        row_after = dbk.select_row_by_rowid(table, rowid)
        if rowid <= len(rows_before):
            assert rows_before[rowid-1] != row_after
        # check the key and in_use
        f = dbs.Fernet(master_key)
        assert key == f.decrypt(row_after[1])
        assert 'in_use' == f.decrypt(row_after[2].encode()).decode()
    
    def test_remove_key(self, dbk, master_key):
        table_num = 0
        rowid = 5
        dbk.remove_key(table_num, rowid)
        # row should not be in use anymore
        assert rowid not in dbk.find_vacancies(table_num, master_key)[1]
        # add it back
        key = dbs.Fernet.generate_key()
        dbk.insert_key(key, table_num, rowid, master_key)

    def test_decrypt_key(self, dbk, master_key):
        key = dbs.Fernet.generate_key()
        f = dbs.Fernet(master_key)
        enc_key = f.encrypt(key)
        assert key == dbk.decrypt_key(enc_key, master_key)
    
    def test_get_rows_and_keys(self, dbk, master_key):
        # table = 'app_keys'
        table_num = 0  # 'app_keys'
        # table = dbk.table_tuple[table_num]

        # add one more
        rowid = 2
        key = b'QJp3y4CS5gPKIQIrZg1m3IzshLMGIamvoaPj9rvSctU='
        dbk.insert_key(key, table_num, rowid, master_key)

        rows_and_keys = dbk.get_rows_and_keys(table_num, master_key)
        assert list(rows_and_keys.keys()) == [2, 5]
        keys = list(rows_and_keys.values())
        assert keys[0] == key
        assert isinstance(keys[1], bytes)

    # this should be further up, but results depend on other tests
    def test_find_vacancies(self, dbk, master_key):
        table_num = 0  # 'app_keys'
        vacancies = dbk.find_vacancies(table_num, master_key)
        num_of_rows = len(dbk.select_all(dbk.table_tuple[table_num]))
        # added keys to rowids 2 and 5, but removed 5
        assert vacancies[1] == [2, 5]
        assert vacancies[0] == [i+1 for i in range(num_of_rows) if i+1 not in [2, 5]]

        table_num = 1  # 'email_keys'
        vacancies = dbk.find_vacancies(table_num, master_key)
        num_of_rows = len(dbk.select_all(dbk.table_tuple[table_num]))
        assert vacancies[1] == []
        assert vacancies[0] == [i+1 for i in range(num_of_rows)]


class TestDBpassword():
    
    def test_add_dummy_data(self, dbp):
        data_type = 1
        table = dbp.table_tuple[data_type]
        rows_before = len(dbp.select_all(table))
        dbp.add_dummy_data(data_type, 1)

        rows_after = len(dbp.select_all(table))
        assert rows_after == rows_before + 1
        

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
            # email 3, app 1
            data = ['username', '00003', 'password', '0000001', 'url']
            dbp.insert_data(data_type, data, row_and_key)
            row_after = dbp.select_row_by_rowid('data', rowid)
            assert row_before != row_after
            for i, item in enumerate(data):
                assert f.decrypt(row_after[i+1].encode()).decode() == item
            # no errors with timestamp
            int(f.decrypt(row_after[-1].encode()).decode())
    
    def test_insert_password_data(self, dbp, rows_and_keys):
        rowid = 1
        row_and_key = (rowid, rows_and_keys[rowid])
        # change app from 1 to 3 and email from 3 to 6
        a = 3
        e = 6
        url = 'www.url.com'
        un = 'new_username'
        pw_data = {'app_name': a, 'email': e, 'url': url, 'username': un}
        dbp.insert_password_data(pw_data, row_and_key)

        row = dbp.select_row_by_rowid('data', rowid)
        f = dbs.Fernet(row_and_key[1])
        assert dbs.cs.decrypt_text(row[1], f) == un
        assert int(dbs.cs.decrypt_text(row[2], f)) == e
        assert dbs.cs.decrypt_text(row[5], f) == url

    def test_get_list(self, dbp, rows_and_keys):
        app_list = dbp.get_list(0, rows_and_keys, False)
        assert app_list == ['app1', 'app3', 'app6']

        app_list = dbp.get_list(1, rows_and_keys)
        assert app_list == [(1, 'mail1@email.com'), (3, 'mail3@email.com'), (6, 'mail6@email.com')]

    def test_find(self, dbp, rows_and_keys):
        search_text = 'app'
        results = dbp.find(0, search_text, rows_and_keys)
        assert results == [(1, 'app1'), (3, 'app3'), (6, 'app6')]

        search_text = '1'
        results = dbp.find(0, search_text, rows_and_keys)
        assert results == [(1, 'app1')]

        search_text = 'MaiL3'
        results = dbp.find(1, search_text, rows_and_keys)
        assert results == [(3, 'mail3@email.com')]

        search_text = 'nonsense'
        results = dbp.find(1, search_text, rows_and_keys)
        assert results == []
    
    def test_delete_data(self, dbp, rows_and_keys):
        rowid = 6
        key = rows_and_keys[rowid]
        f = dbs.Fernet(key)
        # check the 'old' data
        data = ['username', '00003', 'password', '0000001', 'url']
        row = dbp.select_row_by_rowid('data', rowid)
        assert dbs.cs.decrypt_text(row[1], f) == data[0]
        dbp.delete_data(2, 6)

        # now trying the key raises exception
        row = dbp.select_row_by_rowid('data', rowid)
        with pytest.raises(dbs.cs.cryptography.fernet.InvalidToken):
            dbs.cs.decrypt_text(row[1], f) == data[0]

        # insert it back
        dbp.insert_data(2, data, (rowid, key))

    def test_change_password(self, dbp, rows_and_keys):
        rowid = 3
        row_and_key = (rowid, rows_and_keys[rowid])
        dbp.change_password('new_pass', row_and_key)
        # checking
        results = dbp.find_password(0, 1, rows_and_keys)
        assert set((row[3] for row in results)) == set(('password', 'new_pass'))
    
    def test_find_password(self, dbp, rows_and_keys):
        # exception
        data_type = 420
        rowid_to_search = 69
        with pytest.raises(Exception):
            dbp.find_password(data_type, rowid_to_search, rows_and_keys)

        # search email 3
        data_type = 1
        rowid_to_search = 3
        result = dbp.find_password(data_type, rowid_to_search, rows_and_keys)
        assert len(result) == 2

        # search app 1
        data_type = 0
        rowid_to_search = 1
        result = dbp.find_password(data_type, rowid_to_search, rows_and_keys)
        assert len(result) == 2