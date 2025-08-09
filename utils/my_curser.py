import logging
from pymysql.cursors import Cursor
from utils import my_logger as ml

class MyCursor(Cursor):
    def execute(self, query, args=None):
        my_logger = logging.getLogger("Logger")
        my_logger.debug(f"Executing query: {query}")
        result = super().execute(query, args)
        my_logger.debug(f"Query executed successfully: {result}row(s) affected")
        return result
