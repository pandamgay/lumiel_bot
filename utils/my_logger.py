import logging
import sys
from datetime import datetime
import os
import traceback

class MyLogger:

    def __init__(self, is_info_logging : bool):
        self.class_name = self.__class__.__name__
        self.log_path = "../logs/"
        os.makedirs("logs", exist_ok=True)
        self.is_info_logging = is_info_logging

    def initLogger(self):
        __logger = logging.getLogger("Logger")

        # 포매터 정의
        stream_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] ::: %(module)s >>> %(message)s"
        )
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] ::: %(module)s.%(funcName)s:%(lineno)d >>> %(message)s"
        )

        # 핸들러 정의
        stream_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler(f'logs/bot_log_{datetime.now().strftime("%Y%m%d%H%M%S")}.log', mode='w')

        # 핸들러에 포매터 지정
        stream_handler.setFormatter(stream_formatter)
        file_handler.setFormatter(file_formatter)

        # 로그 레벨 정의
        __logger.setLevel(logging.DEBUG)
        if self.is_info_logging:
            stream_handler.setLevel(logging.INFO)

        # 로거 인스턴스에 핸들러 삽입
        __logger.addHandler(stream_handler)
        __logger.addHandler(file_handler)

        return __logger
