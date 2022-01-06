import timeit
import pandas as pd
import numpy as np

import psycopg2
from psycopg2.extensions import register_adapter, AsIs

psycopg2.extensions.register_adapter(np.int64, AsIs)

DB_HOST="35.246.189.236"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="dicn23fnio"
DB_NAME = "TEST"

conn_string = f"dbname={DB_NAME} password={DB_PASS} user={DB_USER} host={DB_HOST} port={DB_PORT}"
connection = psycopg2.connect(conn_string)
connection.autocommit = True
cursor = connection.cursor()

insert_trades = """
    INSERT INTO "BINANCE"."TRADES"
    ("TRA_ID", "TRA_TIMESTAMP", "TRA_CUP_ID", "TRA_PRICE", "TRA_QUANTITY",
        "TRA_QUOTE_QUANTITY", "TRA_BUYER_MAKER")
    VALUES (%s,%s,%s,%s,%s,%s,%s)
"""

datetime_ = pd.to_datetime(1502942428322, unit="ms")
print(datetime_)


to_time = """
args_str = b",".join(
	cursor.mogrify(
		"(%s,%s,%s,%s,%s,%s,%s)", (
			trade["id"], cup_id, pd.to_datetime(trade["time"], unit="ms"),
			trade["price"], trade["qty"], trade["quoteQty"],
			trade["isBuyerMaker"])
	)
	for trade in trades
)
cursor.execute(insert_trades + args_str)
"""

print(timeit.timeit(to_time, globals=globals(), number=240))