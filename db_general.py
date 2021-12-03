import sqlite3
# from db_ini import get_column_names_for_table, get_columns_for_table

# a very not safe way to create SQL commands
# CREATE TABLE table_name (column type etc, column type);
def create_table_command(table_name, column_data):
    columns_and_types = [f'{key} {" ".join(value)}' for key, value in column_data.items()]
    return f'CREATE TABLE {table_name} ({", ".join(columns_and_types)});'


# INSERT INTO table_name (column1, column2, ...) VALUES (? , ?, ...);
def insert_into_command(table_name, columns):
    return f'INSERT INTO {table_name} ({", ".join(columns)}) VALUES ({", ".join(["?" for _ in columns])});'


# UPDATE table_name SET columns[0] = ?, columns[1] = ?, ... WHERE rowid = ?;
def update_command_w_rowid(table_name, columns):
    equalities = [f'{column} = ?' for column in columns]
    return f'UPDATE {table_name} SET {", ".join(equalities)} WHERE rowid = ?;'

# UPDATE table_name SET columns[0] = ?, columns[1] = ?, ... WHERE columns2[0] = ? AND columns2[1] = ? ...;
def update_command_w_where(table_name, columns_to_update, columns_w_condition):
    equalities1 = [f'{column} = ?' for column in columns_to_update]
    equalities2 = [f'{column} = ?' for column in columns_w_condition]
    return f'UPDATE {table_name} SET {", ".join(equalities1)} WHERE {" AND ".join(equalities2)};'


# SELECT columns[0], columns[1], ... FROM table_name;
def select_column_command(table_name, columns):
    return f'SELECT {", ".join(columns)} FROM {table_name};'

# SELECT columns1 FROM table_name WHERE columns[0] = ? AND columns[1] = ?, ...;
def select_columns_where_command(table_name, columns, columns_w_condition):
    conditions = [f'{column} = ?' for column in columns_w_condition]
    return f'SELECT {", ".join(columns)} FROM {table_name} WHERE {" AND ".join(conditions)};'


# database class
class DB_general:
    # db should have a table of tables
    master_table_name = 'tables'
    master_table_columns = {'table_name': ('TEXT', 'NOT NULL', 'UNIQUE'), 
                            'column_data': ('TEXT', 'NOT NULL')}
    master_table_column_names = ('table_name', 'column_data')
    # master_table_columns = get_columns_for_table(master_table_name)
    # master_table_column_names = get_column_names_for_table(master_table_name)
    
    # how to read column data from master table
    @staticmethod
    def string_to_column_data(col_data_as_string : str) -> dict:
        column_data = dict()
        text = col_data_as_string
        while text != '':
            # find the first instance of (,())
            bracket_count = 0
            index = len(text)
            for i, char in enumerate(text):
                if char == '(':
                    bracket_count += 1
                elif char == ')':
                    bracket_count -= 1
                    if bracket_count == 0:
                        index = i
                        break
            item_as_str = text[:index + 1]
            # get column name and data
            name_and_data = item_as_str.split('(')
            name = name_and_data[1].strip(', ')
            data = name_and_data[2].split(',')
            data = tuple(item.strip(")' ") for item in data)
            column_data[name] = data
            # make sure text starts with (
            try:
                text = text[index+1:].strip(', ')
            except IndexError:
                text = ''
        return column_data

    # how to store column data in master table
    @staticmethod
    def column_data_as_string(column_data: dict) -> str:
        list_of_items = [f'({column}, ({", ".join(value)}))' for column, value in column_data.items()]
        return ', '.join(list_of_items)

    # just to make sure columns and data line up
    @staticmethod
    def prepare_to_add_to_master_table(table_name: str, column_dict: dict) -> tuple:
        columns = ('table_name', 'column_data')
        data = (table_name, DB_general.column_data_as_string(column_dict))
        return (columns, data)
    
    @staticmethod
    def table_row_as_dict(row: tuple, columns: tuple) -> dict:
        return {col: item for item, col in zip(row, columns)}


    # initialize just by giving the location of the database, and maybe table_data as a dict
    def __init__(self, filepath_of_db) -> None:
        self.filepath = filepath_of_db
        self.tables = self.get_table_data()
        # make sure master table exists
        if self.tables is None:
            self.tables = dict()
            self.create_table(DB_general.master_table_name, DB_general.master_table_columns)
            # self.tables = {DB_general.master_table_name: DB_general.master_table_columns}
        

    # connect to database
    def connect(self):
        conn = sqlite3.connect(self.filepath)
        cur = conn.cursor()
        return conn, cur

    # get everything in specific columns
    def select_columns(self, table_name, columns):
        conn, cur = self.connect()
        with conn:
            command = select_column_command(table_name, columns)
            try:
                cur.execute(command)
                data = cur.fetchall()
            except sqlite3.OperationalError:
                # presumably table or columns do not exist?
                data = None
        conn.close()
        return data

    # select columns with equality condition on some (possibly other) columns
    def select_columns_by_column_value(self, table_name, columns, column_condition, condition_value):
        conn, cur = self.connect()
        with conn:
            command = select_columns_where_command(table_name, columns, column_condition)
            print(command)
            try:
                cur.execute(command, condition_value)
                data = cur.fetchall()
            except sqlite3.OperationalError:
                # presumably table or columns do not exist?
                data = None
        conn.close()
        return data

    # insert data to specific columns
    def insert(self, table_name, columns, data):
        conn = self.connect()[0]
        with conn:
            command = insert_into_command(table_name, columns)
            try:
                conn.execute(command, data)
            except sqlite3.IntegrityError as error:
                print('Unable to insert:', error)
        conn.close()

    # insert many rows of data
    def insert_many(self, table_name, columns, datalist):
        conn = self.connect()[0]
        with conn:
            command = insert_into_command(table_name, columns)
            try:
                conn.executemany(command, datalist)
            except sqlite3.IntegrityError as error:
                print('Unable to insert:', error)
        conn.close()

    # create a new table
    # column_data as a dict with column name as key, type etc as value (tuple/list)
    def create_table(self, table_name, column_data):
        if column_data is None:
            return
        # check if table already exists
        check_name = self.select_rows_by_column_value(DB_general.master_table_name, DB_general.master_table_column_names[0], table_name)
        # print(f'chack_name is {check_name}')
        if check_name is None or check_name == []:
            success = True
            conn = self.connect()[0]
            with conn:
                command = create_table_command(table_name, column_data)
                try:
                    conn.execute(command)
                    self.tables[table_name] = column_data
                    print('Table', table_name, 'created')
                except sqlite3.OperationalError:
                    # I guess there could be other errors, but...
                    success = False
                    print('this was the command that raised exception')
                    print(command)
                    print('Table', table_name, 'already exists, but its not in', DB_general.master_table_name)
                if check_name is None:
                    command = create_table_command(DB_general.master_table_name, DB_general.master_table_columns)
                    try:
                        conn.execute(command)
                    except sqlite3.OperationalError:
                        # table does not exist by check_name, but somehow we got an error
                        print('problems with', DB_general.master_table_name)
            conn.close()
            if success:
                columns_and_data = DB_general.prepare_to_add_to_master_table(table_name, column_data)
                self.insert(DB_general.master_table_name, *columns_and_data)
                
        else:
            print('Table', table_name, 'already exists')
            print(check_name[0], 'should be the same as', table_name)
        # self.tables[table_name] = column_data

    # remove a table from db
    def drop_table(self, table_name):
        conn, cur = self.connect()
        with conn:
            cur.execute(f'DROP TABLE {table_name};')
            # remove table info from tables
            command = f'DELETE FROM {DB_general.master_table_name} WHERE {DB_general.master_table_column_names[0]} = ?;'
            cur.execute(command, (table_name,))
        conn.close()
        
    # get info on all the tables in the database
    def get_table_data(self):
        raw_table_data = self.select_columns(DB_general.master_table_name, DB_general.master_table_column_names)
        table_data = None
        if raw_table_data is not None:
            table_data = dict()
            for line in raw_table_data:
                table_data[line[0]] = DB_general.string_to_column_data(line[1])
        return table_data

    # update data in specific columns in a row given by rowid
    def update_by_rowid(self, table_name, columns, new_data, rowid):
        conn = self.connect()[0]
        with conn:
            command = update_command_w_rowid(table_name, columns)
            data = list(new_data)
            data.append(rowid)
            conn.execute(command, data)
        conn.close()
    
    # update data with condition on some columns
    def update_by_column_value(self, table_name, columns, new_data, columns_w_condition, condition):
        conn = self.connect()[0]
        with conn:
            command = update_command_w_where(table_name, columns, columns_w_condition)
            data = list(new_data) + list(condition)
            conn.execute(command, data)
        conn.close()

    # hopefully columns are in the correct order here
    def insert_and_create_table_if_needed(self, table_name, column_data, data):
        try:
            self.insert(table_name, column_data.keys(), data)
        except sqlite3.OperationalError:
            self.create_table(table_name, column_data)
            self.insert(table_name, column_data.keys(), data)

    # get info on rows with column = value
    def select_rows_by_column_value(self, table_name, column, value):
        conn, cur = self.connect()
        with conn:
            command = f'SELECT rowid, * FROM {table_name} WHERE {column} = ?;'
            # command = 'SELECT rowid, * FROM ' + table_name + ' WHERE ' + column + ' = ?;'
            try:
                cur.execute(command, (value,))
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                # presumably table does not exist
                rows = None
        conn.close()
        return rows

    def select_rows_by_text_wo_capitalization(self, table_name, column, text):
        conn, cur = self.connect()
        with conn:
            command = f'SELECT rowid, * FROM {table_name} WHERE {column} LIKE ?;'
            # command = 'SELECT rowid, * FROM ' + table_name + ' WHERE ' + column + ' LIKE ?;'
            cur.execute(command, (text,))
            rows = cur.fetchall()
        conn.close()
        return rows
    
    # get info on row with specific rowid
    def select_row_by_rowid(self, table_name, rowid):
        rows = self.select_rows_by_column_value(table_name, 'rowid', rowid)
        return rows[0]

    # get everything from a table
    def select_all(self, table_name):
        conn, cur = self.connect()
        with conn:
            try:
                cur.execute(f'SELECT rowid, * FROM {table_name}')
                all_things = cur.fetchall()
            except sqlite3.OperationalError:
                # table_name not found, presumably
                all_things = None
        conn.close()
        return all_things
    
    # get everything in tables referenced in self.tables
    def get_everything(self):
        everything = dict()
        for table in self.tables:
            everything[table] = self.select_all(table)
        return everything

    # create all the tables according to self.tables
    def create_tables(self):
        for table, columns in self.tables.items():
            self.create_table(table, columns)
    
    # Maybe some more interesting fcns
    # create a csv file containing the data in a table
    def create_csv_file(self, table_name, csv_filename, mode='a'):
        # table_contents = []
        # column_data = self.tables[table_name]
        columns = list(self.tables[table_name].keys())
        data = self.select_columns(table_name, columns)
        if data:
            data.insert(0, columns)
        # make sure Nones are treated correcty
        def stringify(text):
            return '' if text is None else str(text)
        
        with open(csv_filename, mode) as file:
            for line in data:
                line = [stringify(item) for item in line]
                file.write(f'{",".join(line)};\n')

    # backup db to another file
    def backup_db(self, backup_db):
        # backup_db = DB_general(new_filename)
        everything = self.get_table_data()
        for table, col_data in everything.items():
            if table != DB_general.master_table_name:
                backup_db.create_table(table, col_data)
                rows_in_table = self.select_columns(table, col_data.keys())
                backup_db.insert_many(table, col_data.keys(), rows_in_table)
        # print('Are .tables dicts the same?', self.tables == backup_db.tables)
