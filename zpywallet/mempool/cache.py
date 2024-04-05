from urllib.parse import urlparse
import psycopg2
import mysql.connector
import sqlite3
import json
from copy import deepcopy
from ..generated import wallet_pb2


class DatabaseConnection:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.connection = None
        self.cursor = None

    def connect(self):
        raise NotImplementedError("Subclasses must implement connect method")

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

    def connect(self):
        self.connection = psycopg2.connect(**self.connection_params)
        self.cursor = self.connection.cursor()


class MySQLConnection(DatabaseConnection):
    BLOB_TYPE = "BLOB"

    def connect(self):
        self.connection = mysql.connector.connect(**self.connection_params)
        self.cursor = self.connection.cursor()


class SQLiteConnection(DatabaseConnection):
    BLOB_TYPE = "BLOB"

    def connect(self):
        self.connection = sqlite3.connect(**self.connection_params)
        self.cursor = self.connection.cursor()


# This class does not support transactions. That is because the python DB-API
# cursor objects create their own transactions.
class SQLTransactionStorage:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.container = None
        self.cache = []
        self.max_cached = 100

    def connect(self):
        if not self.container:
            protocol = self.connection_params["protocol"]
            params = deepcopy(self.connection_params)
            del params["protocol"]
            if protocol == "postgresql":
                self.container = PostgreSQLConnection(params)
            elif protocol == "mysql":
                self.container = MySQLConnection(params)
            elif protocol == "sqlite":
                self.container = SQLiteConnection(params)
            else:
                raise ValueError("Unsupported protocol")

            self.container.connect()

            try:
                self.create_transactions_table()
                self.create_txos_table()
                self.create_reftxos_table()
                self.create_idtxos_table()
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

    def clear_transactions(self):
        try:
            sql = "DELETE FROM transactions"
            self.container.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error clearing transactions: {e}")

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
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def create_txos_table(self):
        try:
            if not self.container:
                self.connect()

            sql = """
            CREATE TABLE IF NOT EXISTS txos (
                txidn VARCHAR(72) PRIMARY KEY,
                txid VARCHAR(64),
                n INTEGER,
                address VARCHAR(64),
                amount BIGINT,
                output BOOLEAN
            )
            """
            self.container.cursor.execute(sql)

            sql = """
            CREATE VIEW IF NOT EXISTS outtxos AS
                SELECT * FROM txos WHERE output = TRUE;
            """
            self.container.cursor.execute(sql)

            sql = """
            CREATE VIEW IF NOT EXISTS intxos AS
                SELECT * FROM txos WHERE output = FALSE;
            """
            self.container.cursor.execute(sql)

        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def create_reftxos_table(self):
        try:
            if not self.container:
                self.connect()

            sql = f"""
            CREATE TABLE IF NOT EXISTS reftxos (
                txid VARCHAR(64) PRIMARY KEY,
                fine_rawtx {self.container.BLOB_TYPE}
            )
            """

            self.container.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def create_idtxos_table(self):
        try:
            if not self.container:
                self.connect()

            sql = """
            CREATE TABLE IF NOT EXISTS idtxos (
                txid VARCHAR(64) PRIMARY KEY,
            )
            """

            self.container.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def store_transaction(self, transaction):
        try:
            if not self.container:
                self.connect()

            sql = """
            INSERT INTO transactions (txid, timestamp, confirmed, height, total_fee,
                                      fee_metric, rawtx,
                                      txfrom, txto, amount, gas, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            data = (
                transaction.txid,
                transaction.timestamp,
                int(transaction.confirmed),
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
            self.update_cache(transaction)
        except Exception as e:
            raise DatabaseError(f"Error storing transaction: {e}")

    def have_transaction(self, txid):
        try:
            if not self.container:
                self.connect()

            sql = """
            SELECT COUNT(txid) from transactions
            """

            self.container.cursor.execute(sql)
            count = self.container.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def all_txids(self):
        try:
            if not self.container:
                self.connect()

            txids = []

            sql = """
            SELECT txid from transactions
            """

            self.container.cursor.execute(sql)
            txs = self.container.cursor.fetchall()
            txids += [tx[0] for tx in txs]

            sql = """
            SELECT txid from txos
            """

            self.container.cursor.execute(sql)
            txs = self.container.cursor.fetchall()
            txids += [tx[0] for tx in txs]

            return txids

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

    def wipeout_reftxos(self):
        try:
            if not self.container:
                self.connect()

            sql = """
            DELETE FROM reftxos
            """
            self.container.cursor.execute(sql)

        except Exception as e:
            raise DatabaseError(f"Error clearing reftoxs: {e}")

    def get_transaction_by_txid(self, txid):
        for cached_transaction in self.cache:
            if cached_transaction.txid == txid:
                return cached_transaction

        try:
            if not self.container:
                self.connect()

            sql = "SELECT * FROM transactions WHERE txid = %s"
            self.container.cursor.execute(sql, (txid,))
            result = self.container.cursor.fetchone()
            if result:
                return self._sql_to_protobuf(result)
            else:
                return None
        except Exception as e:
            raise DatabaseError(f"Error getting transaction by txid: {e}")

    def store_txo1(self, txid, transaction):
        try:
            if not self.container:
                self.connect()

            sql = """
            INSERT INTO reftxos (txid, fine_rawtx)
            VALUES (?, ?)
            """
            data = (
                txid,
                transaction,
            )
            self.container.cursor.execute(sql, data)

        except Exception as e:
            raise DatabaseError(f"Error storing txo: {e}")

    def store_txo0(self, transaction, n, output=True):

        def get_address(parent, n):
            return parent[n].address

        def get_amount(parent, n):
            return parent[n].amount

        try:
            if not self.container:
                self.connect()

            sql = """
            INSERT INTO txos (txidn, txid, n, address, amount, output)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            outputs = transaction.btclike_transaction.outputs
            inputs = transaction.btclike_transaction.inputs
            data = (
                transaction.txid + ("" if output else "-") + str(n),
                transaction.txid,
                n,
                get_address(outputs if output else inputs, n),
                get_amount(outputs if output else inputs, n),
                output,
            )
            self.container.cursor.execute(sql, data)
        except Exception as e:
            raise DatabaseError(f"Error storing txo: {e}")

    def store_idtxo(self, txid):
        try:
            if not self.container:
                self.connect()

            sql = """
            INSERT INTO idtxo (txid)
            VALUES (?)
            """
            data = (txid,)
            self.container.cursor.execute(sql, data)
        except Exception as e:
            raise DatabaseError(f"Error storing idtxo: {e}")

    def get_rawtx(self, txid):
        try:
            if not self.container:
                self.connect()

            sql = """
            SELECT fine_rawtx from reftxos WHERE txid = ?
            """
            data = (txid,)
            self.container.cursor.execute(sql, data)
            try:
                result = self.container.cursor.fetchone()
                rawtx = wallet_pb2.Transaction()
                rawtx.ParseFromString(result[0])
                return rawtx
            except Exception as e:
                return None
        except Exception as e:
            raise DatabaseError(f"Error storing txo: {e}")

    def get_idtxos(self, batch):
        try:
            if not self.container:
                self.connect()

            sql = """
            SELECT * FROM idtxos
            """
            self.container.cursor.execute(sql)
            try:
                result = self.container.cursor.fetchmany(batch)
                while result is not None:
                    yield [row[0] for row in result]
                    result = self.container.cursor.fetchmany(batch)
            except Exception as e:
                pass
        except Exception as e:
            raise DatabaseError(f"Error storing txo: {e}")

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

    def _btcprotobuf_to_sql(self, transaction_data):
        # Convert BTCLikeTransaction Protobuf message to JSON and serialize to string
        json_data = {
            "fee": transaction_data.fee,
            "inputs": [
                self._btcinprotobuf_to_sql(input_data)
                for input_data in transaction_data.inputs
            ],
            "outputs": [
                self._btcoutprotobuf_to_sql(output_data)
                for output_data in transaction_data.outputs
            ],
        }
        return json.dumps(json_data)

    def _btcinprotobuf_to_sql(self, txi_data):
        # Convert BTCLikeInput Protobuf message to JSON and serialize to string
        json_data = {
            "txid": txi_data.txid,
            "index": txi_data.index,
            "amount": txi_data.amount,
            # "witness_data": txi_data.witness_data,  # We DO NOT save witness data for now
            "address": txi_data.address,
        }
        return json.dumps(json_data)

    def _btcoutprotobuf_to_sql(self, txo_data):
        # Convert BTCLikeOutput Protobuf message to JSON and serialize to string
        json_data = {
            "amount": txo_data.amount,
            "address": txo_data.address,
            "index": txo_data.index,
            # "witness_data": txo_data.witness_data,  # We DO NOT save witness data for now
            "spent": txo_data.spent,
        }
        return json.dumps(json_data)

    def update_cache(self, transaction):
        if len(self.cache) >= self.max_cached:
            self.cache.pop(0)
        self.cache.append(transaction)

    def empty_cache(self):
        self.cache = []

    def _sql_to_protobuf(self, row):
        # Parse transaction data from SQL result
        btclike_transaction = json.loads(row[6])

        # Create Protobuf message
        transaction = wallet_pb2.Transaction()
        transaction.txid = row[0]
        transaction.timestamp = row[1]
        transaction.confirmed = row[2]
        transaction.height = row[3]
        transaction.total_fee = row[4]
        transaction.fee_metric = row[5]
        transaction.btclike_transaction.fee = btclike_transaction["fee"]
        transaction.btclike_transaction.inputs.extend(btclike_transaction["inputs"])
        transaction.btclike_transaction.outputs.extend(btclike_transaction["outputs"])
        transaction.ethlike_transaction.txfrom = row[7]
        transaction.ethlike_transaction.txto = row[8]
        transaction.ethlike_transaction.amount = row[9]
        transaction.ethlike_transaction.gas = row[10]
        transaction.ethlike_transaction.data = row[11]
        return transaction


class DatabaseError(Exception):
    pass
