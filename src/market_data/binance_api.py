#!/root/market_data/python-env/bin/python

import http
import os

import binance
import psycopg2
import pandas as pd
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
from binance.exceptions import BinanceAPIException



############################## SETUP ENVIRONMENT ##############################
psycopg2.extensions.register_adapter(np.int64, AsIs)

DB_HOST="35.246.189.236"
DB_PORT="5432"
DB_USER="postgres"
DB_PASS="dicn23fnio"
DB_NAME = "TEST"

conn_string = f"dbname={DB_NAME} password={DB_PASS} user={DB_USER} host={DB_HOST} port={DB_PORT}"

# Sebastians personal api keys needed to use python-binance package
binance_key = "GImqrPPoDPmgV13GcRpKJW0hPod2zRtRqN2k3p934MWUUCGAw9IlFvwqORxrcvuS"
binance_secret = "KXygPUSY83sE0a6FGOShrUuXcwoilDFKjQXUg6tglvWK4mZwcv7W09uUyz1KeEAV"

class TooManyRequestsExcept(Exception):
    pass
############################ DEFINE VARIABLES #################################
# Changes go here

currency_pair_sql = "'BTCUSDT'"
cup_code = "BTCUSDT"

base_code = "BTC"
base_type = "cryptocurrency"
quote_code = "USDT"
quote_type = "cryptocurrency"

############################ DEFINE SQL STATEMENTS ############################
# Get the id of the currency pair
query_cup_id = f"""
    SELECT "CUP_ID"
    FROM "PROD_001"."CURRENCY_PAIR"
    WHERE "CUP_CODE" = {currency_pair_sql}
"""
# Insert the trade data into TEST db schema
insert_trades = b"""
    INSERT INTO "BINANCE"."TRADES"
    ("TRA_ID", "TRA_CUP_ID", "TRA_TIMESTAMP", "TRA_PRICE", "TRA_QUANTITY",
        "TRA_QUOTE_QUANTITY", "TRA_BUYER_MAKER")
    VALUES 
"""
# Insert a new currency into operations schema
insert_currency = """
    INSERT INTO "PROD_001"."CURRENCY"
    ("CUR_ID", "CUR_CODE", "CUR_TYPE")
    VALUES (NEXTVAL('"PROD_001"."SEQ_CUR_ID"'),%s,%s)
"""

query_cur_ids = """
    SELECT "CUR_ID", "CUR_CODE"
    FROM "PROD_001"."CURRENCY"
    WHERE "CUR_CODE" IN (%s, %s) 
"""
def get_trade_id(db_connection, cup_id):
    query = f"""
        SELECT MAX("TRA_ID") 
        FROM "BINANCE"."TRADES"
        WHERE "TRA_CUP_ID" = {cup_id}
    """
    return pd.read_sql_query(query, db_connection).values[0][0]

# Yield new currency pair
def populate_pairs(db_connection, pairs):
    """
    Inputs: List of dicts with pairs aka {"BASE": "LINK", "QUOTE": "BTC"}
    """
    query_keys = """
        SELECT *
        FROM "PROD_001"."CURRENCY"
    """
    keys = pd.read_sql_query(query_keys, db_connection)
    query = """
        INSERT INTO "PROD_001"."CURRENCY_PAIR"
        ("CUP_ID", "CUP_CUR_ID_BASE", "CUP_CUR_ID_QUOTE", "CUP_CODE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_CUP_ID"'),%s,%s,%s)
    """
    with db_connection.cursor() as cursor:
        for pair in pairs:
            cur_id_base = keys[keys["CUR_CODE"]==pair["BASE"]]["CUR_ID"].iloc[0]
            cur_id_quote = keys[keys["CUR_CODE"]==pair["QUOTE"]]["CUR_ID"].iloc[0]
            pair_code = pair["BASE"]+pair["QUOTE"]

            values = (cur_id_base, cur_id_quote, pair_code)
            cursor.execute(query, values)

########################## MAIN FUNCTION ######################################
def main(connection, client, cup_id):
    if not connection or connection.closed != 0:
        connection = psycopg2.connect(conn_string)
        connection.autocommit = True
    if not client:
        client = binance.Client(binance_key, binance_secret)
    trades = [0]
    trade_id = get_trade_id(connection, cup_id) + 1
    with connection.cursor() as cursor:
        while len(trades) > 0:
            for i in range(240):
                try:
                    trades = client.get_historical_trades(
                        symbol=cup_code, limit=1000, fromId=str(trade_id)
                    )

                    args_str = b",".join(
                        cursor.mogrify(
                            "(%s,%s,%s,%s,%s,%s,%s)", (
                                trade["id"], cup_id,
                                pd.to_datetime(trade["time"], unit="ms"),
                                trade["price"], trade["qty"], trade["quoteQty"],
                                trade["isBuyerMaker"])
                        )
                        for trade in trades
                    )

                    trade_id += 1000
                    cursor.execute(insert_trades + args_str)
                except BinanceAPIException as error:
                    if error.status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
                        raise TooManyRequestsExcept("ERROR: Exceeded rate limit")
                    else:
                        raise error


try:
    db_connection = psycopg2.connect(conn_string)
    db_connection.autocommit = True
    binance_client = binance.Client(binance_key, binance_secret)
    print("SUCCESS: DB and API connection created")
except psycopg2.Error as error:
    print(error)
except binance.exceptions as error:
    print(error)

with db_connection.cursor() as cur:
    values = (base_code, quote_code)
    cur.execute(query_cur_ids, values)
    currencies = {row[1]: row[0] for row in cur.fetchall()}

    if base_code not in currencies.keys():
        currency_info = (base_code, base_type)
        cur.execute(insert_currency, currency_info)

    if quote_code not in currencies.keys():
        currency_info = (quote_code, quote_type)
        cur.execute(insert_currency, currency_info)

    populate_pairs(db_connection,
                   [{"BASE": base_code, "QUOTE": quote_code}])
    cup_id = pd.read_sql_query(query_cup_id, db_connection).values[0][0]
    print("SUCCESS: NEW PAIRS POPULATED")
try:
    main(db_connection, binance_client, cup_id)
except TooManyRequestsExcept:
    print("Stopped due to excess requests")
    os.abort()