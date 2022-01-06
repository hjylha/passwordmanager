# paths at index 0 are defaults, files at these paths may be overwritten
# paths to long term files should be from index 1 forwards
salt_path = ('salt_default.txt', 'data/salt.txt')
db_auth_path = ('data/auth.db',)
db_keys_path = ('data/keys.db',)
db_data_path = ('data/data.db',)

paths = (salt_path, db_auth_path, db_keys_path, db_data_path)