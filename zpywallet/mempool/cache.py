from base64 import b64decode, b64encode
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
    def connect(self):
        self.connection = psycopg2.connect(**self.connection_params)
        self.cursor = self.connection.cursor()


class MySQLConnection(DatabaseConnection):
    def connect(self):
        self.connection = mysql.connector.connect(**self.connection_params)
        self.cursor = self.connection.cursor()


class SQLiteConnection(DatabaseConnection):
    def connect(self):
        self.connection = sqlite3.connect(**self.connection_params)
        self.cursor = self.connection.cursor()


class SQLTransactionStorage:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.connection = None
        self.cache = []
        self.max_cached = 100

    def connect(self):
        if not self.connection:
            protocol = self.connection_params["protocol"]
            params = deepcopy(self.connection_params)
            del params["protocol"]
            if protocol == "postgresql":
                self.connection = PostgreSQLConnection(params)
            elif protocol == "mysql":
                self.connection = MySQLConnection(params)
            elif protocol == "sqlite":
                self.connection = SQLiteConnection(params)
            else:
                raise ValueError("Unsupported protocol")

            self.connection.connect()

            try:
                self.create_table()
            except DatabaseError:
                pass

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()

    def reconnect(self):
        if self.connection:
            self.connection.reconnect()

    def begin_transaction(self):
        self.connection.connect()
        self.connection.cursor.execute("BEGIN")

    def commit_transaction(self):
        self.connection.cursor.execute("COMMIT")

    def rollback_transaction(self):
        self.connection.cursor.execute("ROLLBACK")

    def clear_transactions(self):
        try:
            sql = "DELETE FROM transactions"
            self.connection.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error clearing transactions: {e}")

    def create_table(self):
        try:
            if not self.connection:
                self.connect()

            protocol = self.connection_params.get("protocol")
            if protocol == "postgresql":
                sql = """
                CREATE TABLE IF NOT EXISTS transactions (
                    txid VARCHAR(255) PRIMARY KEY,
                    timestamp TIMESTAMP,
                    confirmed BOOLEAN,
                    height BIGINT,
                    total_fee BIGINT,
                    fee_metric INT,
                    btclike_transaction JSONB,
                    ethlike_transaction JSONB
                )
                """
            elif protocol == "mysql":
                sql = """
                CREATE TABLE IF NOT EXISTS transactions (
                    txid VARCHAR(255) PRIMARY KEY,
                    timestamp TIMESTAMP,
                    confirmed BOOLEAN,
                    height BIGINT,
                    total_fee BIGINT,
                    fee_metric INT,
                    btclike_transaction JSON,
                    ethlike_transaction JSON
                )
                """
            elif protocol == "sqlite":
                sql = """
                CREATE TABLE IF NOT EXISTS transactions (
                    txid TEXT PRIMARY KEY,
                    timestamp INTEGER,
                    confirmed INTEGER,
                    height INTEGER,
                    total_fee INTEGER,
                    fee_metric INTEGER,
                    btclike_transaction JSON,
                    ethlike_transaction JSON
                )
                """
            else:
                raise DatabaseError(f"Unknown protocol: {protocol}")

            self.connection.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def store_transaction(self, transaction):
        try:
            if not self.connection:
                self.connect()

            sql = """
            INSERT INTO transactions (txid, timestamp, confirmed, height, total_fee,
                                      fee_metric, btclike_transaction,
                                      ethlike_transaction)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            data = (
                f"'{transaction.txid}'",
                transaction.timestamp,
                int(transaction.confirmed),
                transaction.height,
                transaction.total_fee,
                transaction.fee_metric,
                f"'{self._btcprotobuf_to_sql(transaction.btclike_transaction)}'",
                f"'{self._ethprotobuf_to_sql(transaction.ethlike_transaction)}'",
            )
            self.connection.cursor.execute(sql, data)
            self.update_cache(transaction)
        except Exception as e:
            raise DatabaseError(f"Error storing transaction: {e}")

    def have_transaction(self, txid):
        try:
            if not self.connection:
                self.connect()

            sql = """
            SELECT COUNT(txid) from transactions
            """

            self.connection.cursor.execute(sql)
            count = self.connection.cursor.fetchone()[0]
            return count > 0
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def all_txids(self):
        try:
            if not self.connection:
                self.connect()

            sql = """
            SELECT txid from transactions
            """

            self.connection.cursor.execute(sql)
            txs = self.connection.cursor.fetchall()
            return [tx[0] for tx in txs]

        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def delete_transaction(self, txid):
        try:
            if not self.connection:
                self.connect()

            sql = """
            DELETE FROM transactions WHERE txid == ?
            """

            data = (txid,)
            self.connection.cursor.execute(sql, data)
        except Exception as e:
            raise DatabaseError(f"Error deleting transaction: {e}")

    def get_transaction_by_txid(self, txid):
        for cached_transaction in self.cache:
            if cached_transaction.txid == txid:
                return cached_transaction

        try:
            if not self.connection:
                self.connect()

            sql = "SELECT * FROM transactions WHERE txid = %s"
            self.connection.cursor.execute(sql, (txid,))
            result = self.connection.cursor.fetchone()
            if result:
                return self._sql_to_protobuf(result)
            else:
                return None
        except Exception as e:
            raise DatabaseError(f"Error getting transaction by txid: {e}")

    def get_transaction_by_address(self, address):
        for cached_transaction in self.cache:
            if address in [
                i.address for i in cached_transaction.btclike_transaction.inputs
            ] or address in [
                o.address for o in cached_transaction.btclike_transaction.outputs
            ]:
                return cached_transaction
        try:
            if not self.connection:
                self.connect()

            sql = self._get_transaction_by_address_query()
            self.connection.cursor.execute(sql, (address,))
            result = self.connection.cursor.fetchall()
            transactions = [self._sql_to_protobuf(row) for row in result]
            return transactions
        except Exception as e:
            raise DatabaseError(f"Error getting transactions by address: {e}")

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

    def _ethprotobuf_to_sql(self, transaction_data):
        # Convert EthLikeTransaction Protobuf message to JSON and serialize to string
        json_data = {
            "txfrom": transaction_data.txfrom,
            "txto": transaction_data.txto,
            "amount": transaction_data.amount,
            "gas": transaction_data.gas,
            "data": b64encode(transaction_data.data).decode("utf-8"),
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
        ethlike_transaction = json.loads(row[7])

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
        transaction.ethlike_transaction.txfrom = ethlike_transaction["txfrom"]
        transaction.ethlike_transaction.txto = ethlike_transaction["txto"]
        transaction.ethlike_transaction.amount = ethlike_transaction["amount"]
        transaction.ethlike_transaction.gas = ethlike_transaction["gas"]
        transaction.ethlike_transaction.data = b64decode(ethlike_transaction["data"])
        return transaction

    def _get_transaction_by_address_query(self):
        protocol = self.connection_params.get("protocol")
        if protocol == "postgresql":
            return "SELECT * FROM transactions WHERE btclike_transaction->'inputs' @> %s \
                OR btclike_transaction->'outputs' @> %s"
        elif protocol == "mysql":
            return "SELECT * FROM transactions WHERE JSON_CONTAINS(btclike_transaction->'inputs', %s) \
                OR JSON_CONTAINS(btclike_transaction->'outputs', %s)"
        elif protocol == "sqlite":
            return "SELECT * FROM transactions WHERE btclike_transaction LIKE '%' || ? || '%' \
                OR btclike_transaction LIKE '%' || ? || '%'"


class DatabaseError(Exception):
    pass
