import psycopg2
import mysql.connector
import sqlite3
import json
from ..generated import wallet_pb2


class DatabaseConnection:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.connection = None
        self.cache = []

    def connect(self):
        raise NotImplementedError("Subclasses must implement connect method")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def reconnect(self):
        self.disconnect()
        self.connect()


class PostgreSQLConnection(DatabaseConnection):
    def connect(self):
        self.connection = psycopg2.connect(**self.connection_params)


class MySQLConnection(DatabaseConnection):
    def connect(self):
        self.connection = mysql.connector.connect(**self.connection_params)


class SQLiteConnection(DatabaseConnection):
    def connect(self):
        self.connection = sqlite3.connect(**self.connection_params)


class SQLTransactionStorage:
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.connection = None
        self.max_cached = 100

    def connect(self):
        if not self.connection:
            protocol = self.connection_params.get("protocol")
            if protocol == "postgresql":
                self.connection = PostgreSQLConnection(self.connection_params)
            elif protocol == "mysql":
                self.connection = MySQLConnection(self.connection_params)
            elif protocol == "sqlite":
                self.connection = SQLiteConnection(self.connection_params)
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
                    btc_fee BIGINT,
                    eth_gas BIGINT,
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
                    btc_fee BIGINT,
                    eth_gas BIGINT,
                    btclike_transaction JSON,
                    ethlike_transaction JSON
                )
                """
            elif protocol == "sqlite":
                sql = """
                CREATE TABLE IF NOT EXISTS transactions (
                    txid TEXT PRIMARY KEY,
                    timestamp TEXT,
                    confirmed INTEGER,
                    height INTEGER,
                    total_fee INTEGER,
                    fee_metric INTEGER,
                    btc_fee INTEGER,
                    eth_gas INTEGER,
                    btclike_transaction TEXT,
                    ethlike_transaction TEXT
                )
                """

            self.connection.cursor.execute(sql)
        except Exception as e:
            raise DatabaseError(f"Error creating table: {e}")

    def store_transaction(self, transaction):
        try:
            if not self.connection:
                self.connect()

            sql = """
            INSERT INTO transactions (txid, timestamp, confirmed, height, total_fee,
                                      fee_metric, btc_fee, eth_gas, btclike_transaction,
                                      ethlike_transaction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            data = (
                transaction.txid,
                transaction.timestamp,
                transaction.confirmed,
                transaction.height,
                transaction.total_fee,
                transaction.fee_metric,
                transaction.btc_fee,
                transaction.eth_gas,
                self._protobuf_to_sql(transaction.btclike_transaction),
                self._protobuf_to_sql(transaction.ethlike_transaction),
            )
            self.connection.cursor.execute(sql, data)
            self.update_cache(transaction)
        except Exception as e:
            raise DatabaseError(f"Error storing transaction: {e}")

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

    def _protobuf_to_sql(self, transaction_data):
        # Convert Protobuf message to JSON and serialize to string
        json_data = {
            "fee": transaction_data.fee,
            "inputs": [
                self._protobuf_to_sql(input_data)
                for input_data in transaction_data.inputs
            ],
            "outputs": [
                self._protobuf_to_sql(output_data)
                for output_data in transaction_data.outputs
            ],
        }
        return json.dumps(json_data)

    def update_cache(self, transaction):
        if len(self.cache) >= self.max_cached:
            self.cache.pop(0)
        self.cache.append(transaction)

    def _sql_to_protobuf(self, row):
        # Parse transaction data from SQL result
        btclike_transaction = json.loads(row[8])
        ethlike_transaction = json.loads(row[9])

        # Create Protobuf message
        transaction = wallet_pb2.Transaction()
        transaction.txid = row[0]
        transaction.timestamp = row[1]
        transaction.confirmed = row[2]
        transaction.height = row[3]
        transaction.total_fee = row[4]
        transaction.fee_metric = row[5]
        transaction.btc_fee = row[6]
        transaction.eth_gas = row[7]
        transaction.btclike_transaction.fee = btclike_transaction["fee"]
        transaction.btclike_transaction.inputs.extend(btclike_transaction["inputs"])
        transaction.btclike_transaction.outputs.extend(btclike_transaction["outputs"])
        transaction.ethlike_transaction.txfrom = ethlike_transaction["txfrom"]
        transaction.ethlike_transaction.txto = ethlike_transaction["txto"]
        transaction.ethlike_transaction.amount = ethlike_transaction["amount"]
        transaction.ethlike_transaction.gas = ethlike_transaction["gas"]
        transaction.ethlike_transaction.data = ethlike_transaction["data"]
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
