
# import dbs
from typing import ParamSpec
from dbs import PasswordNotFoundError, DB_auth, DB_keys, DB_password


class PM():
    def __init__(self, db_auth, db_keys, db_data):
        self.dba = db_auth
        self.dbk = db_keys
        self.dbp = db_data
        # should this be here?
        self.master_key = None
    
    # get salt (from somewhere in the files...)
    def get_salt(self):
        pass
    
    # check that password is in db, and get master key
    def check_password(self, password):
        try:
            encrypted_m_key = self.dba.check_password(password)
            self.master_key = self.dba.decrypt_key(encrypted_m_key, password, self.get_salt())
            # return self.dba.decrypt_key(encrypted_m_key, password, salt)
            return True
        except PasswordNotFoundError:
            # print('Password not in database.')
            return False
        
        
    