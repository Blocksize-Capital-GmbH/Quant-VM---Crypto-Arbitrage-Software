import time
import datetime

import psycopg2

import src.helpers
import src.util.util
import src.sql_queries
import numpy as np


def make_milli_timestamp():
    return int(np.ceil(time.time() * 1000))


write_db_order_log = src.sql_queries.error_log_to_db()

time_1 = int(time.time())
time_2 = src.util.unix_milli()
time_3 = datetime.datetime.now()
time_4 = time.time() * 1000
time_5 = make_milli_timestamp()

times = [time_1, time_2, time_3, time_4, time_5]
logger_wrapper = src.util.LoggerWrapper(1)

with src.helpers.DBConnector(logger_wrapper.logger) as connection:
    for i, time in enumerate(times):
        print(i+1)
        print(time, type(time))
        try:
            time = src.helpers.convert_timestamp_to_datetime(time, logger_wrapper)
            cursor = connection.cursor()
            values = (
                1, 'bdbb8931-2e7a-4535-afe2-05b59f03ebf1', time, "TEST", "-",
                "-", 0, f"time{i+1}"
            )

            cursor.execute(write_db_order_log, values)
        except (Exception, psycopg2.Error) as errm:
            print(errm)



"""
db_connection = src.helpers.DBconnection()
db_connection.connection = None
logger = src.util.base_logger("döner", 1, db_connection)

try:
    cursor = db_connection.connection.cursor()
except (Exception, psycopg2.Error) as errm:
    logger.error(errm)
    db_connection.create_db_connection()
    cursor = db_connection.connection.cursor()
"""

if __name__ == "main":
    pass