'''names of tables and columns'''

table_data: dict[str, dict[str, dict[str, tuple[str]]]] = dict()
type_tuples: dict[str, tuple[str]] = dict()

# the auth db
table_data['auth'] = {'auth': {'hash': ('TEXT', 'NOT NULL'),
                            'master_key': ('TEXT', 'NOT NULL'),
                            'date_modified': ('TEXT', 'NOT NULL')}}
type_tuples['auth'] = ('hash', 'key', 'normal')

# the keys db
table_data['keys'] = dict()
table_data['keys']['app_keys'] = {'key': ('TEXT', 'NOT NULL'),
                                'in_use': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
table_data['keys']['email_keys'] = {'key': ('TEXT', 'NOT NULL'),
                                'in_use': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
table_data['keys']['data_keys'] = {'key': ('TEXT', 'NOT NULL'),
                                'in_use': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
type_tuples['keys'] = ('key', 'normal', 'normal')

# the actual data db
table_data['password'] = dict()
table_data['password']['apps'] = {'app': ('TEXT', 'NOT NULL'),
                                'num_of_instances': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
table_data['password']['emails'] = {'email': ('TEXT', 'NOT NULL'),
                                'num_of_instances': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
table_data['password']['data'] = {'username': ('TEXT', 'NOT NULL'),
                                'email': ('TEXT', 'NOT NULL'),
                                'password': ('TEXT', 'NOT NULL'),
                                'app_name': ('TEXT', 'NOT NULL'),
                                'url': ('TEXT', 'NOT NULL'),
                                'date_modified': ('TEXT', 'NOT NULL')}
type_tuples['password'] = tuple('normal' for _ in range(6))