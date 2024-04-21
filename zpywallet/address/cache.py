from urllib.parse import urlparse
import time
from copy import deepcopy
from ..generated import wallet_pb2


class DatabaseConnection:
    def __init__(self, dbmodule, connection_params):
        self.dbmodule = dbmodule
        self.connection_params = connection_params
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = self.dbmodule.connect(**self.connection_params)
        self.cursor = self.connection.cursor()

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def reconnect(self):
        self.disconnect()
        self.connect()

    @staticmethod
    def parse_uri(uri):
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == "sqlite":
            # For SQLite URIs with a local file
            connection_params = {
                "protocol": "sqlite",
                "database": parsed_uri.path.lstrip("/"),
            }
        else:
            # For other database types
            connection_params = {
                "protocol": parsed_uri.scheme,
                "host": parsed_uri.hostname,
                "port": parsed_uri.port,
                "database": parsed_uri.path.lstrip("/"),
                "user": parsed_uri.username,
                "password": parsed_uri.password,
            }
        return connection_params

    def parse_connection_params(self):
        if isinstance(self.connection_params, str):
            return self.parse_uri(self.connection_params)
        else:
            return self.connection_params


class PostgreSQLConnection(DatabaseConnection):
    BLOB_TYPE = "BYTEA"

    def REPLACE(sql, id):
        return (
            "INSERT INTO "
            + sql
            + f" ON CONFLICT ({id}) DO UPDATE SET {id} = EXCLUDED.{id}"
        )

    def __init__(self, psycopg2, connection_params):
        super().__init__(psycopg2, connection_params)


class MySQLConnection(DatabaseConnection):
    BLOB_TYPE = "BLOB"

    def REPLACE(self, sql, _=None):
        return "REPLACE INTO " + sql

    def __init__(self, mysql_connector, connection_params):
        super().__init__(mysql_connector, connection_params)


class SQLiteConnection(DatabaseConnection):
    BLOB_TYPE = "BLOB"

    def REPLACE(self, sql, _=None):
        return "INSERT INTO OR REPLACE " + sql

    def __init__(self, sqlite3, connection_params):
        super().__init__(sqlite3, connection_params)


# This class does not support transactions. That is because the python DB-API
# cursor objects create their own transactions.
class SQLTransactionStorage:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.container = None

    def connect(self):
        if not self.container:
            protocol = self.connection_params["protocol"]
            params = deepcopy(self.connection_params)
            del params["protocol"]
            if protocol == "postgresql":
                import psycopg2

                self.container = PostgreSQLConnection(psycopg2, params)
            elif protocol == "mysql":
                import mysql.connector

                self.container = MySQLConnection(mysql.connector, params)
            elif protocol == "sqlite":
                import sqlite3

                self.container = SQLiteConnection(sqlite3, params)
            else:
                raise ValueError("Unsupported protocol")

            self.container.connect()

            try:
                self.create_metadata_table()
                self.create_transactions_table()
            except DatabaseError:
                pass

    def disconnect(self):
        if self.container:
            self.container.disconnect()

    def reconnect(self):
        if self.container:
            self.container.reconnect()

    def commit(self):
        if self.container:
            self.container.connection.commit()

    def rollback(self):
        try:
            if self.container:
                self.container.connection.rollback()
        except Exception:
            pass

    # DANGER this wipes out the entire transaction cache
    def clear_transactions(self):
        try:
            sql = "DELETE FROM transactions"
            self.container.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error clearing transactions: {e}")

    def create_metadata_table(self):
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS metadata (
                zpywallet_const VARCHAR(9) PRIMARY KEY,
                height INTEGER
                )
                """

            self.container.cursor.execute(sql)

            sql = self.container.REPLACE(
                """
            metadata (zpywallet_const, height) VALUES (?, ?)
            """,
                "zpywallet_const",
            )

            self.container.cursor.execute(sql, ("zpywallet", 0))
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def create_transactions_table(self):
        try:
            if not self.container:
                self.connect()

            sql = """
            CREATE TABLE IF NOT EXISTS transactions (
                txid VARCHAR(64) PRIMARY KEY,
                timestamp TIMESTAMP,
                confirmed BOOLEAN,
                height BIGINT,
                total_fee BIGINT,
                fee_metric INTEGER,
                rawtx TEXT,
                txfrom TEXT,
                txto TEXT,
                amount INTEGER,
                gas INTEGER,
                data TEXT
            )
            """

            self.container.cursor.execute(sql)

            sql = """
            CREATE VIEW IF NOT EXISTS confirmed_transactions AS
            SELECT * FROM transactions WHERE confirmed = TRUE
            """

            self.container.cursor.execute(sql)

            sql = """
            CREATE VIEW IF NOT EXISTS unconfirmed_transactions AS
            SELECT * FROM transactions WHERE confirmed = FALSE
            """

            self.container.cursor.execute(sql)

        except Exception as e:
            raise DatabaseError(f"Error creating transactions table: {e}")

    def get_block_height(self):
        try:
            if not self.container:
                self.connect()

            sql = """
            SELECT height from metadata
            WHERE zpywallet_const = 'zpywallet'
            """

            self.container.cursor.execute(sql)
            height = self.container.cursor.fetchone()[0]
            return height
        except Exception as e:
            raise DatabaseError(f"Error getting block height from database: {e}")

    def set_block_height(self, height):
        try:
            if not self.container:
                self.connect()

            sql = self.container.REPLACE(
                """
            metadata (height) VALUES (?, ?)
            """,
                "zpywallet_const",
            )

            self.container.cursor.execute(sql, (height))
        except Exception as e:
            raise DatabaseError(f"Error setting block height in database: {e}")

    def store_transaction(self, transaction):
        try:
            if not self.container:
                self.connect()

            sql = self.container.REPLACE(
                """
            transactions (txid, timestamp, confirmed, height, total_fee,
                                      fee_metric, rawtx,
                                      txfrom, txto, amount, gas, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                "txid",
            )
            data = (
                transaction.txid,
                transaction.timestamp,
                transaction.confirmed,
                transaction.height,
                transaction.total_fee,
                transaction.fee_metric,
                transaction.SerializeToString(),
                transaction.ethlike_transaction.txfrom or "",
                transaction.ethlike_transaction.txto or "",
                transaction.ethlike_transaction.amount,
                transaction.ethlike_transaction.gas,
                "",  # f"'{b64encode(transaction.ethlike_transaction.data).decode("utf-8")}'"
            )
            self.container.cursor.execute(sql, data)
        except Exception as e:
            raise DatabaseError(f"Error storing transaction: {e}")

    def have_transaction(self, txid):
        try:
            if not self.container:
                self.connect()

            sql = f"""
            SELECT COUNT(txid) from transactions
            WHERE txid = {txid} LIMIT 1
            """

            self.container.cursor.execute(sql)
            count = self.container.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def delete_dropped_txids(self):
        try:
            if not self.container:
                self.connect()

            # Drop all unconfirmed transactions that are more than 2 weeks old
            sql = f"""
            DELETE from transactions WHERE confirmed = FALSE AND  timestamp < {int(time.time())-1209600}
            """

            self.container.cursor.execute(sql)

        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def delete_transaction(self, txid):
        try:
            if not self.container:
                self.connect()

            sql = """
            DELETE FROM transactions WHERE txid == ?
            """

            data = (txid,)
            self.container.cursor.execute(sql, data)

            sql = """
            DELETE FROM txos WHERE txid == ?
            """
            self.container.cursor.execute(sql, data)

        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def get_transaction_by_txid(self, txid):
        try:
            if not self.container:
                self.connect()

            sql = "SELECT rawtx FROM transactions WHERE txid = %s"
            self.container.cursor.execute(sql, (txid,))
            result = self.container.cursor.fetchone()
            if result:
                transaction = wallet_pb2.Transaction()
                transaction.ParseFromString(result[0])
                return transaction
            else:
                return None
        except Exception as e:
            raise DatabaseError(f"Error getting transaction by txid: {e}")

    def get_transactions_by_address(self, address):
        try:
            if not self.container:
                self.connect()

            sql = """
            SELECT txid from txos WHERE address = ?
            """
            data = (address,)
            self.container.cursor.execute(sql, data)
            result = self.container.cursor.fetchall()
            txids = [r[0] for r in result]
            transactions = []
            for txid in txids:
                sql = """
                SELECT * FROM transactions WHERE txid = ?
                """
                self.container.cursor.execute(sql, (txid,))
                row = self.container.cursor.fetchone()
                transactions.append(self._sql_to_protobuf(row))
            return transactions
        except Exception as e:
            raise DatabaseError(f"Error storing txo: {e}")


class DatabaseError(Exception):
    pass
