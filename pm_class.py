from typing import Optional

import dbs
from dbs import PasswordNotFoundError, DB_auth, DB_keys, DB_password

# make a basic check to see if email could be an email address
def is_valid_email(email: str) -> bool:
    # no spaces
    if ' ' in email:
        return False
    # @ should be in email once and . after that
    if '@' not in email:
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False
    if '.' not in parts[1]:
        return False
    return True

# check if url has at least one . and no spaces
def is_valid_url(url: str) -> bool:
    if ' ' in url:
        return False
    if '.' not in url:
        return False
    return True


# class combining all the databases together
class PM():
    def __init__(self, salt: bytes, db_auth: DB_auth, db_keys: DB_keys, db_data: DB_password) -> None:
        self.dba = db_auth
        self.dbk = db_keys
        self.dbp = db_data
        self.salt = salt
        # should these be here?
        self.master_key = None
        self.app_list = None
        self.email_list = None
    
    # get salt (from somewhere in the files...)
    # def get_salt(self) -> bytes:
    #     # TODO: all of these salt things
    #     return b'\xc1\x95\xe15=\tm\xef\xecTH\x8e\xf5;/l'

    # # generate salt (and put it in some file)
    # def generate_salt(self) -> None:
    #     pass

    # add password (and generate master key) the first time
    def add_master_password(self, password: str) -> None:
        self.master_key = self.dba.add_password(password, self.salt)
        # self.master_key = self.dba.decrypt_key(encrypted_m_key, password, self.salt)
    
    # check that password is in db, and get master key
    def check_master_password(self, password: str) -> bool:
        try:
            encrypted_m_key = self.dba.check_password(password)
            self.master_key = self.dba.decrypt_key(encrypted_m_key, password, self.salt)
            # return self.dba.decrypt_key(encrypted_m_key, password, salt)
            return True
        except PasswordNotFoundError:
            # print('Password not in database.')
            return False
        
    # change the password (and change master key, optionally)
    def change_master_password(self, old_password: str, new_password: str, change_master_key: bool =True) -> None:
        rowid, e_master_key = self.dba.check_password(old_password, True)
        master_key = None
        if not change_master_key:
            # self.check_master_password(old_password)
            master_key = self.dba.decrypt_key(e_master_key, old_password, self.salt)
        self.master_key = self.dba.add_password(new_password, self.salt, master_key, rowid)

    
    # into the real business
    # app_or_email = 0 for app, 1 for email
    def find_info(self, app_or_email: int, name: str) -> list[tuple[int, str]]:
        if not self.master_key:
            raise Exception('Master key not active')
        # get in-use rows and corresponding keys
        rows_and_keys = self.dbk.get_rows_and_keys(app_or_email, self.master_key)
        # search through the rows
        return self.dbp.find(app_or_email, name, rows_and_keys)
    
    def get_name_list(self, app_or_email: int) -> list[tuple[int, str]]:
        if not self.master_key:
            raise Exception('Master key not active')
        # get in-use rows and corresponding keys
        rows_and_keys = self.dbk.get_rows_and_keys(app_or_email, self.master_key)
        # the_list = self.dbp.get_list(app_or_email, rows_and_keys)
        # if app_or_email:
        #     self.email_list = the_list
        # else:
        #     self.app_list = the_list
        return self.dbp.get_list(app_or_email, rows_and_keys)
        # return the_list

    def set_name_lists(self) -> None:
        self.app_list = self.get_name_list(0)
        self.email_list = self.get_name_list(1)
        
    # make sure there are rows for new data
    def check_num_of_rows(self, type_num: int) -> None:
        len_k = len(self.dbk.select_all(self.dbk.table_tuple[type_num]))
        len_d = len(self.dbp.select_all(self.dbp.table_tuple[type_num]))
        if (row_num := (len_k - len_d)) > 0:
            self.dbp.add_dummy_data(type_num, row_num)

    # app_or_email = 0 for app, 1 for email
    def add_info(self, app_or_email: int, name: str) -> Optional[int]:
        if not self.master_key:
            raise Exception('Master key not active')
        # check if name is already in db (not sure if this should be part of UI)
        if app_or_email:
            if not is_valid_email(name):
                # raise Exception('not a valid email address')
                name = '-'
            # list_of_similar_names = (name for _, name in self.find_info(app_or_email, name))
            findings = dbs.find_from_list(name, self.email_list, True)
        else:
            findings = dbs.find_from_list(name, self.app_list, True)
        if findings:
            return findings[0][0]
        # if name is not in db, add it
        # make sure there are rows to add to
        self.check_num_of_rows(app_or_email)
        # get rowid and key, and insert
        row_and_key = self.dbk.add_new_key(app_or_email, self.master_key)
        self.dbp.insert_data(app_or_email, (name, str(0)), row_and_key)
        if app_or_email:
            self.email_list.append((row_and_key[0], name))
        else:
            self.app_list.append((row_and_key[0], name))
        return row_and_key[0]

    # TODO: check that no invalid tokens exist
    def check_keys(self):
        if not self.master_key:
            raise Exception('Master key not active')
        pass

    # get the possible rowids for app and email
    def prepare_to_add_password(self, app: str, email: str) -> dict[str, list[tuple[int, str]]]:
        findings = {app: self.find_info(0, app)}
        findings[email] = self.find_info(1, email)
        return findings

    # add password, if (app, username) is not in db
    def add_password(self, username: str, email_rowid: int, password: str, app_rowid: int, url: str) -> bool:
        if not self.master_key:
            raise Exception('Master key not active')
        if not self.app_list or self.email_list:
            self.set_name_lists()
        # check if app and username already in db
        app = [app_name for r, app_name in self.app_list if r == app_rowid][0]
        if self.find_password(app, True, username):
            # should it raise an exception?
            return False
        # add new key
        row_and_key = self.dbk.add_new_key(2, self.master_key)
        # make sure there are rows
        self.check_num_of_rows(2)
        # insert data in the correct format
        data = {'username': username, 'email': email_rowid, 'password': password, 'app_name': app_rowid, 'url': url}
        self.dbp.insert_password_data(data, row_and_key)
        return True
    
    # just add the password
    def force_add_password(self, username: str, email: str, password: str, app: str, url: str) -> None:
        if not self.master_key:
            raise Exception('Master key not active')
        if not self.app_list or self.email_list:
            self.set_name_lists()
        # add new key
        row_and_key = self.dbk.add_new_key(2, self.master_key)
        email_rowid = self.add_info(1, email)
        app_rowid = self.add_info(0, app)
        # make sure there are rows
        self.check_num_of_rows(2)
        # insert data in the correct format
        data = {'username': username, 'email': email_rowid, 'password': password, 'app_name': app_rowid, 'url': url}
        self.dbp.insert_password_data(data, row_and_key)
        # self.add_password(username, email_rowid, password, app_rowid, url)

    # find user and password info for app
    def find_password(self, app: str, exact_match: bool = False, username: Optional[str] = None) -> list[tuple[int, str, str, str, str, str]]:
        if not self.master_key:
            raise Exception('Master key not active')
        if not self.app_list:
            self.set_name_lists()
        app_info = dbs.find_from_list(app, self.app_list, exact_match)
        password_info = []
        for info in app_info:
            # print('app info has rowid:', info[0])
            pw_rows = self.dbp.find_password(0, info[0], self.dbk.get_rows_and_keys(2, self.master_key))
            # show the actual email and password
            if username is None:
                for i, row in enumerate(pw_rows):
                    row = list(row)
                    row[4] = info[1]
                    row[2] = [e for r, e in self.email_list if r == row[2]][0]
                    pw_rows[i] = tuple(row)
                password_info += pw_rows
            # if we also want to match username
            else:
                for i, row in enumerate(pw_rows):
                    if row[1] == username:
                        row = list(row)
                        row[4] = info[1]
                        row[2] = [e for r, e in self.email_list if r == row[2]][0]
                        password_info.append(tuple(row))
        return password_info

    # changing and removing password depends on the rowid
    def change_password(self, rowid: int, new_password: str) -> None:
        if not self.master_key:
            raise Exception('Master key not active')
        row_and_key = (rowid, self.dbk.get_rows_and_keys(2, self.master_key)[rowid])
        self.dbp.change_password(new_password, row_and_key)
    
    # change other data (new_data = {'username': str, 'email': str, 'app_name': str, 'url': str})
    def update_password_data(self, rowid: int, new_data: dict[str, str]) -> None:
        if 'email' in new_data:
            new_data['email'] = self.add_info(1, new_data['email'])
        if 'app_name' in new_data:
            new_data['app_name'] = self.add_info(0, new_data['app_name'])
        row_and_key = (rowid, self.dbk.get_rows_and_keys(2, self.master_key)[rowid])
        self.dbp.insert_password_data(new_data, row_and_key)

    # overwrite password row and corresponding key
    def delete_password(self, rowid: int) -> None:
        if not self.master_key:
            raise Exception('Master key not active')
        # overwrite the row
        self.dbp.delete_data(2, rowid)
        # remove the corresponding key and change it to be vacant
        self.dbk.remove_key(2, rowid)
        
    