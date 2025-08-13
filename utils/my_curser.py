import logging
from pymysql.cursors import Cursor
from pymysql import OperationalError
from utils import my_logger as ml

class MyCursor(Cursor):
    def __init__(self, connection, *args, **kwargs):
        super().__init__(connection, *args, **kwargs)
        self.my_logger = logging.getLogger("Logger")
        self._connection = connection

    def execute(self, query, args=None):
        conn = self._connection

        self.my_logger.debug(f"Executing query: {query}")
        try:
            conn.ping(reconnect=True)
        except OperationalError as e:
            if e.args[0] in (2006, 2013):
                self.my_logger.warning("Connection lost, attempting to reconnect...")
                conn.connect()  # 재연결 시도
            else:
                raise
        result = super().execute(query, args)
        self.my_logger.debug(f"Query executed successfully: {result}row(s) affected")
        return result
