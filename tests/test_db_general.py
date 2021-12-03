from pathlib import Path
import pytest

import fix_imports
import db_general
from db_general import DB_general


# testing fcns creating sql commands

def test_create_table_command():
    table = 'Table_Name'
    column_data = {'column1': ('TEXT', 'UNIQUE'), 'column2': ('INTEGER', 'NOT NULL')}
    command = 'CREATE TABLE Table_Name (column1 TEXT UNIQUE, column2 INTEGER NOT NULL);'
    assert db_general.create_table_command(table, column_data) == command


def test_insert_into_command():
    table = 'Table_Name'
    columns = ('column1', 'column2', 'column3')
    command = 'INSERT INTO Table_Name (column1, column2, column3) VALUES (?, ?, ?);'
    assert db_general.insert_into_command(table, columns) == command


def test_update_command_w_rowid():
    table = 'Table_Name'
    columns = ('column1', 'column2')
    command = 'UPDATE Table_Name SET column1 = ?, column2 = ? WHERE rowid = ?;'
    assert db_general.update_command_w_rowid(table, columns) == command

def test_update_command_w_where():
    table = 'Table_Name'
    columns = ('column1', 'column2')
    columns_w_condition = ('rowid', 'column1')
    command = 'UPDATE Table_Name SET column1 = ?, column2 = ? WHERE rowid = ? AND column1 = ?;'
    assert db_general.update_command_w_where(table, columns, columns_w_condition) == command


def test_select_column_command():
    table = 'Table_Name'
    columns = ('column1', 'column2')
    command = 'SELECT column1, column2 FROM Table_Name;'
    assert db_general.select_column_command(table, columns) == command

def test_select_columns_where_command():
    table = 'Table_Name'
    columns = ('column1', 'column2')
    columns_w_cond = ('column3', 'column4', 'column5')
    command = 'SELECT column1, column2 FROM Table_Name WHERE column3 = ? AND column4 = ? AND column5 = ?;'
    assert db_general.select_columns_where_command(table, columns, columns_w_cond) == command


# testing DG_general
@pytest.fixture
def db():
    db_path = Path('test_db.db')
    yield DB_general(db_path)
    db_path.unlink()


# def test_master_table_columns():
#     columns = DB_general.master_table_column_names
#     assert columns == db_ini.get_column_names_for_table('tables')
#     column_data = DB_general.master_table_columns
#     assert column_data == db_ini.get_columns_for_table('tables')


def test_string_to_column_data():
    columns_as_str = '(table_name, (TEXT, NOT NULL, UNIQUE)), (column_data, (TEXT, NOT NULL))'
    column_data = DB_general.string_to_column_data(columns_as_str)
    assert column_data == DB_general.master_table_columns
    # do one item tuples cause problems?
    column_data = {'Col1': ('TEXT',), 'Col2': ('TEXT',), 'Col3': ('INTEGER',)}
    column_data_as_str = '(Col1, (TEXT)), (Col2, (TEXT)), (Col3, (INTEGER))'
    assert column_data == DB_general.string_to_column_data(column_data_as_str)

def test_column_data_as_string():
    columns_as_str = '(table_name, (TEXT, NOT NULL, UNIQUE)), (column_data, (TEXT, NOT NULL))'
    column_data_as_str = DB_general.column_data_as_string(DB_general.master_table_columns)
    assert columns_as_str == column_data_as_str

def test_prepare_to_add_to_master_table():
    table = 'Table_Name'
    column_data = {'Col1': ('TEXT', 'UNIQUE')}
    result = DB_general.prepare_to_add_to_master_table(table, column_data)
    assert result[0] == ('table_name', 'column_data')
    assert result[1] == ('Table_Name', '(Col1, (TEXT, UNIQUE))')

def test_table_row_as_dict():
    columns = ('col1', 'col2', 'col3')
    row = (1, 2, 3)
    row_dict = DB_general.table_row_as_dict(row, columns)
    assert row_dict == {'col1': 1, 'col2': 2, 'col3': 3}


def test_DB_general(db):
    # db = DB_general('test_db.db')
    assert 'tables' in db.tables
    assert set(['table_name', 'column_data']) == set(db.tables['tables'].keys())

def test_connect(db):
    conn, cur = db.connect()
    assert isinstance(conn, db_general.sqlite3.Connection)
    assert isinstance(cur, db_general.sqlite3.Cursor)
    conn.close()
    with pytest.raises(db_general.sqlite3.ProgrammingError):
        conn.in_transaction


def test_select_columns(db):
    table = 'tables'
    columns = ('table_name', 'column_data')
    column_data = db.select_columns(table, columns)
    row = ('tables', '(table_name, (TEXT, NOT NULL, UNIQUE)), (column_data, (TEXT, NOT NULL))')
    assert row in column_data
    # trying to select from nonexistent table
    assert db.select_columns('non_existing', ('Not', 'Existing')) is None

def test_select_columns_by_column_value(db):
    table = 'tables'
    columns = ('table_name',)
    columns_condition = ('table_name',)
    condition_value = ('tables',)
    selection = db.select_columns_by_column_value(table, columns, columns_condition, condition_value)
    assert table in selection[0]
    assert selection[0][0] == table
    # trying to select from nonexistent table
    assert db.select_columns_by_column_value('non_existing', ('Not', 'Existing'), ('Not',), (1,)) is None

    columns = ('table_name', 'column_data')
    selection = db.select_columns_by_column_value(table, columns, columns_condition, condition_value)
    assert table in selection[0]
    assert 'table_name' in selection[0][1]

    columns_condition = ('table_name', 'column_data')
    condition_value = (table, '(table_name, (TEXT, NOT NULL, UNIQUE)), (column_data, (TEXT, NOT NULL))')
    assert table in selection[0]
    assert 'column_data' in selection[0][1]
    

def test_insert(db):
    table = 'tables'
    columns = ('table_name', 'column_data')
    data = ('test_name', 'not valid column data here')
    db.insert(table, columns, data)

    # select content and see if inserted data is there
    content = db.select_columns(table, columns)
    the_rows = [row for row in content if 'test_name' in row]
    assert the_rows[0][1] == 'not valid column data here'
    # not sure if it is necessary to remove this row, but let's do it anyway
    conn, cur = db.connect()
    with conn:
        cur.execute('DELETE FROM tables WHERE table_name = ? AND column_data = ?', data)
    conn.close()
    # trying to insert to a nonexistent table
    with pytest.raises(db_general.sqlite3.OperationalError):
        db.insert('nonexistent', ('nothing',), (0,))

def test_insert_many(db):
    table = 'tables'
    columns = ('table_name', 'column_data')
    search_name = 'searchable'
    data = (('name1', search_name), ('name2', search_name), ('name3', search_name))
    db.insert_many(table, columns, data)

    content = db.select_columns(table, columns)
    rows = [row for row in content if search_name in row]
    assert len(rows) == len(data)
    assert ['name1', 'name2', 'name3'] == [row[0] for row in rows]

    # trying to insert to a nonexistent table
    with pytest.raises(db_general.sqlite3.OperationalError):
        db.insert('nonexistent', ('nothing',), ((0,),(1,)))


def test_create_table(db):
    table = 'New_Table'
    column_data = {'Col1': ('TEXT', 'NOT NULL', 'UNIQUE'), 'Col2': ('INTEGER')}
    db.create_table(table, column_data)

    # this table should have been inserted to 'tables' table
    tables = db.select_columns_by_column_value('tables', ('table_name', 'column_data'), ('table_name',), (table,))
    assert table in tables[0]
    assert 'Col2' in tables[0][1]

    # it should also be in db.tables dictionary
    assert table in db.tables
    assert column_data == db.tables[table]
    
    # try to insert something to this table
    columns = ('Col1', 'Col2')
    db.insert(table, columns, ('jee', 37))
    data = db.select_columns(table, ('Col1', 'Col2'))
    assert data[0] == ('jee', 37)

def test_drop_table(db):
    table = 'New_Table'
    column_data = {'Col1': ('TEXT', 'NOT NULL', 'UNIQUE'), 'Col2': ('INTEGER')}
    db.create_table(table, column_data)
    # New_Table should be empty
    assert db.select_columns(table, column_data.keys()) == []
    
    db.drop_table(table)
    # table should be removed from the master table
    table_names = [row[0] for row in db.select_columns('tables', ('table_name',))]
    assert table not in table_names
    # when table is dropped, inserting should raise an exception
    with pytest.raises(db_general.sqlite3.OperationalError):
        db.insert(table, column_data.keys(), ('some_text', 42))
    # dropping a nonexistent table should raise an exception
    with pytest.raises(db_general.sqlite3.OperationalError):
        db.drop_table('nonexistent_test_table')



# fixture with an added table, and maybe some rows inserted
@pytest.fixture
def db1(db):
    # dbg = next(db())
    dbg = db
    table = 'test_table'
    column_data = {'Col1': ('TEXT',), 'Col2': ('TEXT',), 'Col3': ('INTEGER',)}
    dbg.create_table(table, column_data)
    columns = ('Col1', 'Col2', 'Col3')
    datalist = [('a', 'b', 1), ('c', 'd', 2), ('e', 'f', 3)]
    dbg.insert_many(table, columns, datalist)
    # create an empty table with same columns as above
    empty_table = 'empty_table'
    dbg.create_table(empty_table, column_data)
    return dbg


def test_get_table_data(db1):
    table_data = db1.get_table_data()
    assert 'tables' in table_data
    assert table_data == db1.tables
    # db1 tables should be in table_data
    assert 'empty_table' in table_data
    assert 'test_table' in table_data
    column_data = {'Col1': ('TEXT',), 'Col2': ('TEXT',), 'Col3': ('INTEGER',)}
    assert table_data['test_table'] == column_data


def test_update_by_rowid(db1):
    table = 'test_table'
    columns = ('Col2', 'Col3')
    new_value = ('X', 99)
    db1.update_by_rowid(table, columns, new_value, 1)
    # did it update?
    rows = db1.select_columns_by_column_value(table, columns, ('rowid',), (1,))
    assert rows[0] == new_value

def test_update_by_column_value(db1):
    table = 'test_table'
    columns = ('Col2', 'Col3')
    new_value = ('X', 99)
    columns_w_cond = ('Col1', 'Col2')
    cond = ('c', 'd')
    db1.update_by_column_value(table, columns, new_value, columns_w_cond, cond)
    # did it update?
    rows = db1.select_columns_by_column_value(table, columns, ('rowid',), (2,))
    assert rows[0] == new_value

# less important fcns
def test_insert_and_create_table_if_needed(db1):
    table = 'Brand_New_Table'
    column_data = {'Just_1_column': ('INTEGER', 'NOT NULL')}
    data = (28,)
    # make sure this table does not exist
    assert table not in db1.get_table_data()
    db1.insert_and_create_table_if_needed(table, column_data, data)
    # was table created and data inserted?
    table_data = db1.get_table_data()
    assert table in table_data
    rows = db1.select_columns(table, ('Just_1_column',))
    assert rows[0][0] == 28

def test_select_rows_by_column_value(db1):
    table = 'test_table'
    column = 'Col2'
    value = 'f'
    rows = db1.select_rows_by_column_value(table, column, value)
    assert rows[0] == (3, 'e', 'f', 3)

def test_select_rows_by_text_wo_capitalization(db1):
    table = 'test_table'
    column = 'Col2'
    text = 'F'
    rows = db1.select_rows_by_text_wo_capitalization(table, column, text)
    assert rows[0] == (3, 'e', 'f', 3)

def test_select_row_by_rowid(db1):
    table = 'test_table'
    rowid = 3
    row = db1.select_row_by_rowid(table, rowid)
    assert row == (3, 'e', 'f', 3)

def test_select_all(db1):
    table = 'test_table'
    data = [(1, 'a', 'b', 1), (2, 'c', 'd', 2), (3, 'e', 'f', 3)]
    assert db1.select_all(table) == data

def test_get_everything(db1):
    everything = db1.get_everything()
    assert 'tables' in everything
    assert 'test_table' in everything
    assert 'empty_table' in everything
    tables_rows = [(1, 'tables', DB_general.column_data_as_string(DB_general.master_table_columns))]
    tables_rows.append((2, 'test_table', '(Col1, (TEXT)), (Col2, (TEXT)), (Col3, (INTEGER))'))
    tables_rows.append((3, 'empty_table', '(Col1, (TEXT)), (Col2, (TEXT)), (Col3, (INTEGER))'))
    all_stuff = {'tables': tables_rows}
    all_stuff['test_table'] = [(1, 'a', 'b', 1), (2, 'c', 'd', 2), (3, 'e', 'f', 3)]
    all_stuff['empty_table'] = []
    assert all_stuff == everything

def test_create_tables(db):
    # make sure test_table and empty_table do not exist at first
    assert 'test_table' not in db.tables
    assert 'empty_table' not in db.tables
    col_data = {'Col1': ('TEXT',), 'Col2': ('TEXT',), 'Col3': ('INTEGER',)}
    db.tables['test_table'] = col_data
    db.tables['empty_table'] = col_data
    db.create_tables()
    # trying to insert to nonexistent tables should bring out errors
    db.insert('test_table', col_data.keys(), ('a', 'b', 1))
    db.insert('empty_table', col_data.keys(), ('x', 'y', 0))
    assert db.select_all('test_table') == [(1, 'a', 'b', 1)]
    assert db.select_all('empty_table') == [(1, 'x', 'y', 0)]


# back to more interesting fcns
def test_create_csv_file(db1):
    filepath = Path(__file__).parent / 'test.csv'
    db1.create_csv_file('test_table', filepath)
    # check the contents of this file
    with open(filepath, 'r') as f:
        assert f.readline().strip() == 'Col1,Col2,Col3;'
        assert f.readline().strip() == 'a,b,1;'
        assert f.readline().strip() == 'c,d,2;'
        assert f.readline().strip() == 'e,f,3;'
    # remove the csv file after the test
    filepath.unlink()


@pytest.fixture
def db_backup():
    db_path = Path('test_db_backup.db')
    yield DB_general(db_path)
    db_path.unlink()

def test_backup_db(db1, db_backup):
    backup_tables = db_backup.get_table_data()
    assert 'test_table' not in backup_tables
    assert 'empty_table' not in backup_tables
    tables = db1.get_table_data()
    db1.backup_db(db_backup)
    backup_tables = db_backup.get_table_data()
    assert tables == backup_tables
    for table in tables:
        assert db1.select_all(table) == db_backup.select_all(table)
    assert db1.tables == db_backup.tables
    assert db1.get_everything() == db_backup.get_everything()
