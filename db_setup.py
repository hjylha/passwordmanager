'''names of tables and columns'''

# the keys db
keys_table_data = dict()
keys_table_data['auth'] = {'hash': ('TEXT', 'NOT NULL'),
                            'master_key': ('TEXT', 'NOT NULL'),
                            'date_modified': ('TEXT', 'NOT NULL')}
keys_table_data['app_keys'] = {'key': ('TEXT', 'NOT NULL'),
                                'in_use': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
keys_table_data['email_keys'] = {'key': ('TEXT', 'NOT NULL'),
                                'in_use': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
keys_table_data['data_keys'] = {'key': ('TEXT', 'NOT NULL'),
                                'in_use': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}

# the actual data db
data_db_table_data = dict()
data_db_table_data['apps'] = {'app': ('TEXT', 'NOT NULL'),
                                'num_of_instances': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
data_db_table_data['emails'] = {'email': ('TEXT', 'NOT NULL'),
                                'num_of_instances': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
data_db_table_data['data'] = {'username': ('TEXT', 'NOT NULL'),
                                'email': ('TEXT', 'NOT NULL'),
                                'password': ('TEXT', 'NOT NULL'),
                                'app_name': ('TEXT', 'NOT NULL'),
                                'url': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}