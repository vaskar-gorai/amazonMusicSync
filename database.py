import sqlite3, sys

def createConnection(databaseName):
    connection = None
    try:
        connection = sqlite3.connect(databaseName)
    except sqlite3.Error as e:
        sys.stderr.write(str(e)+'\n')
    finally:
        return connection

def insertTable(tableName, columns, connection):
    try:
        assert (type(tableName) == str), "Table Name must be a string"
        assert (type(columns) == tuple), "Column must be tuple"
        assert (type(connection) == sqlite3.Connection), "connection not an Connection object"
        cursor = connection.cursor()
        command = """CREATE TABLE %s%s""" % (tableName, str(columns))
        cursor.execute(command)
        connection.commit()
        return 0
    except sqlite3.Error as e:
        sys.stderr.write(str(e)+'\n');
        return 1
    except AssertionError as e:
        sys.stderr.write(str(e)+'\n')
        return 1

def searchRows(what, searchParam, tableName, connection):
    try:
        assert (type(connection) == sqlite3.Connection), "connection not an Connection object"
        assert (type(tableName) == str), "Tablename must be string"
        assert (type(searchParam) == str), "searchParam must be string"
        assert (type(what) == str), "what must be string"
        cursor = connection.cursor()
        result = cursor.execute("SELECT name FROM sqlite_master")
        assert ((tableName,) in result.fetchall()), "Tablename not found in database"
        command = """SELECT %s FROM %s WHERE %s""" % (what, tableName, searchParam)
        result = cursor.execute(command)
        connection.commit()
        return result.fetchall()
    except sqlite3.Error as e:
        sys.stderr.write(str(e)+'\n')
        return 1
    except AssertionError as e:
        sys.stderr.write(str(e)+'\n')
        return 1

def insertRowInTable(row, tableName, connection):
    try:
        assert (type(connection) == sqlite3.Connection), "connection not an Connection object"
        assert (type(row) == tuple), "Row must be of tuple type"
        assert (type(tableName) == str), "Tablename must be string"
        cursor = connection.cursor()
        result = cursor.execute("SELECT name FROM sqlite_master")
        assert ((tableName,) in result.fetchall()), "Tablename not found in database"
        command = """INSERT INTO %s VALUES %s""" % (tableName, str(row))
        result = cursor.execute(command)
        connection.commit()
        return 0
    except sqlite3.Error as e:
        sys.stderr.write(str(e)+'\n')
        return 1
    except AssertionError as e:
        sys.stderr.write(str(e)+'\n')
        return 1

def deleteRowInTable(searchParam, tableName, connection):
    try:
        assert (type(connection) == sqlite3.Connection), "connection not an Connection object"
        assert (type(searchParam) == str), "Searchparam must be of str type"
        assert (type(tableName) == str), "Tablename must be string"
        cursor = connection.cursor()
        result = cursor.execute("SELECT name FROM sqlite_master")
        assert ((tableName,) in result.fetchall()), "Tablename not found in database"
        command = "DELETE FROM %s WHERE %s" %(tableName, searchParam)
        result = cursor.execute(command)
        connection.commit()
        return 0
    except sqlite3.Error as e:
        sys.stderr.write(str(e)+'\n')
        return 1
    except AssertionError as e:
        sys.stderr.write(str(e)+'\n')
        return 1

def closeConnection(connection):
    try:
        assert (type(connection) == sqlite3.Connection), "connection not an Connection object"
        connection.commit()
        connection.close()
        return 0
    except sqlite3.Error as e:
        sys.stderr.write(str(e)+'\n')
        return 1
    except AssertionError as e:
        sys.stderr.write(str(e)+'\n')
        return 1
