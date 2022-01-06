import pandas as pd
import numpy as np
from typing import List

import psycopg2
from psycopg2.extensions import register_adapter, AsIs

import src.util
import src.helpers

# Setup system connection
mode = "DEV"

psycopg2.extensions.register_adapter(np.int64, AsIs)
logger_wrapper = src.util.LoggerWrapper(algo_id=None)
db_connector = src.helpers.DBConnector(logger=logger_wrapper.logger, mode=mode)

############################# SET PARAMETERS ###################################
# To-be populated currency pairs
pairs = [
	{"BASE": "LINK", "QUOTE": "EUR"},
	{"BASE": "BTC", "QUOTE": "EUR"},
	{"BASE": "BTC", "QUOTE": "USD"},
	{"BASE": "ETH", "QUOTE": "EUR"},
]
# To-be populated echange currency pair associations
exchange_names = ['BITFINEX', 'BITPANDA',
				  'KRAKEN']  # Single quotation marks !!!
currency_pairs = ['LINKEUR']

# To-be populated algo exchange associations
algos = ['A-tests-multi-lateral']
algo_exchanges = ['BITFINEX', 'BITPANDA', 'KRAKEN']

# To-be populated algo currency pair associations
cups_algo = ['LINKEUR']


############################# DEFINE FUNCTIONS #################################
def get_algo_registry(db_connection):
	query = """
        SELECT *
        FROM "public"."algo_registry" AS "ALR"
        --JOIN "public"."algo_configuration" AS "ALC"
        --ON "ALR"."id" = "ALC"."id_algo"
        WHERE "name" = 'A-tests-multi-lateral'
    """
	return pd.read_sql_query(query, db_connection)


def migrate_algo_registry(db_connection, data):
	query_migrate = """
        INSERT INTO "PROD_001"."ALGO_REGISTRY" 
            ("ALR_ID", "ALR_NAME", "ALR_DESCRIPTION", "ALR_STATUS")
        VALUES (NEXTVAL('"PROD_001"."SEQ_ALR_ID"'),%s,%s,%s)
    """
	query_lookup = """
        SELECT "ALR_ID"
        FROM "PROD_001"."ALGO_REGISTRY"
        WHERE "ALR_NAME" IN (%s)
    """
	lookup = {}
	with db_connection.cursor() as cursor:
		for row in data.itertuples(index=False):
			values = (row.name, row.description, row.status)
			cursor.execute(query_migrate, values)
			cursor.execute(query_lookup, (row.name,))
			lookup[row.id] = cursor.fetchall()[0][0]
	return lookup


def get_algo_config(db_connection):
	query = """
        SELECT *
        FROM "public"."algo_configuration"
    """
	config_df = pd.read_sql_query(query, db_connection)
	# Make entries atomic
	for row in config_df.itertuples():
		field_entries = str(row.property_value).replace(" ", "").split(",")
		if len(field_entries) > 1:
			for item in field_entries:
				new_row = [[row.property_name, item, row.id_algo]]
				new_row = pd.DataFrame(data=new_row, columns=config_df.columns)
				config_df = pd.concat([config_df, new_row])
				"""config_df.append(
					{"property_name": row.property_name,
					"property_value": item,
					"id_alog": row.id_algo},
					ignore_index=True
				)"""

			config_df.drop(index=row.Index, inplace=True)
	return config_df


def migrate_algo_config(db_connection, data, lookup):
	query_migrate = """
        INSERT INTO "PROD_001"."ALGO_CONFIGURATION"
        ("ALC_ID", "ALC_ALR_ID", "ALC_NAME", "ALC_VALUE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_ALC_ID"'),%s,%s,%s)
    """
	with db_connection.cursor() as cursor:
		for row in data.itertuples():
			values = (
			lookup[row.id_algo], row.property_name, row.property_value)
			cursor.execute(query_migrate, values)


def get_currency(db_connection):
	query = """
        SELECT *
        FROM "public"."currency"
        ORDER BY "id" ASC
    """
	return pd.read_sql_query(query, db_connection)


def migrate_currency(db_connection, data):
	query_migrate = """
        INSERT INTO "PROD_001"."CURRENCY"
        ("CUR_ID", "CUR_CODE", "CUR_TYPE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_CUR_ID"'),%s,%s)
    """
	with db_connection.cursor() as cursor:
		for row in data.itertuples():
			values = (row.code, row.type)
			cursor.execute(query_migrate, values)


def get_exchanges(db_connection):
	query = """
        SELECT *
        FROM "public"."exchanges"
        ORDER BY "id" ASC
    """
	return pd.read_sql_query(query, db_connection)


def migrate_exchanges(db_connection, data):
	query_migrate = """
        INSERT INTO "PROD_001"."EXCHANGE"
        ("EXC_ID", "EXC_NAME")
        VALUES (NEXTVAL('"PROD_001"."SEQ_EXC_ID"'),%s)
    """
	with db_connection.cursor() as cursor:
		for row in data.itertuples():
			values = (row.name,)
			cursor.execute(query_migrate, values)


def get_pairs(db_connection):
	query = """
        SELECT *
        FROM "public"."currency_pairs"
        ORDER BY "id" ASC
    """
	return pd.read_sql_query(query, db_connection)


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
        ("CUR_ID", "CUR_CUP_ID_BASE", "CUR_CUP_ID_QUOTE", "CUP_CODE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_CUP_ID"'),%s,%s,%s)
    """
	with db_connection.cursor() as cursor:
		for pair in pairs:
			cur_id_base = keys[keys["CUR_CODE"] == pair["BASE"]]["CUR_ID"].iloc[
				0]
			cur_id_quote = \
			keys[keys["CUR_CODE"] == pair["QUOTE"]]["CUR_ID"].iloc[0]
			pair_code = pair["BASE"] + pair["QUOTE"]

			values = (cur_id_base, cur_id_quote, pair_code)
			cursor.execute(query, values)


# TODO complement exchange specific technicals: precision, step size, etc.

def populate_exchange_currency_pair(db_connection, exchange_names,
									currency_pairs):
	"""
	Inputs: exchange_names, currency_pairs list e.g. ["'BITFINEX'"]
	Write cross product to db
	"""
	if len(exchange_names) == 1:
		exchange_names.append(exchange_names[0])
	if len(currency_pairs) == 1:
		currency_pairs.append(currency_pairs[0])

	exchange_names, currency_pairs = tuple(exchange_names), tuple(
		currency_pairs)
	query_keys = """
        SELECT
            "EXC_ID",
            "CUP_ID"
        FROM
            "PROD_001"."CURRENCY_PAIR",
            "PROD_001"."EXCHANGE"
        WHERE
            "EXC_NAME" IN {}
            AND "CUP_CODE" IN {}
        ORDER BY "EXC_ID"
    """.format(exchange_names, currency_pairs)
	keys = pd.read_sql_query(query_keys, db_connector.connection)

	query = """
        INSERT INTO "PROD_001"."EXCHANGE_CURRENCY_PAIR"
        ("ECP_ID", "ECP_EXC_ID", "ECP_CUP_ID","ECP_BASE_PREC","ECP_QUOTE_PREC",
         "ECP_MIN_QTY", "ECP_STEPSIZE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_EXC_ID"'),%s,%s)
    """

	with db_connection.cursor() as cursor:
		for row in keys.itertuples():
			values = (row.EXC_ID, row.CUP_ID)
			cursor.execute(query, values)


def populate_algo_exchange_asso(db_connection, algo_names: List,
								exchanges: List):
	"""
	Writes cross product of algo_names and exchanges to table
	 "PROD_001"."ALGO_EXCHANGE_ASSOCIATION"
	"""

	if len(exchanges) == 1:
		exchanges.append(exchanges[0])
	if len(algo_names) == 1:
		algo_names.append(algo_names[0])

	algo_names = tuple(algo_names)
	exchanges = tuple(exchanges)

	query_keys = """
        SELECT
        	"ALR_ID",
        	"EXC_ID"
        FROM
        	"PROD_001"."ALGO_REGISTRY",
        	"PROD_001"."EXCHANGE"
        WHERE
        	"ALR_NAME" IN {}
        	AND "EXC_NAME" IN {}
    """.format(algo_names, exchanges)

	query_populate = """
        INSERT INTO "PROD_001"."ALGO_EXCHANGE_ASSOCIATION"
        ("AEA_ID", "AEA_ALR_ID", "AEA_EXC_ID")
        VALUES (NEXTVAL('"PROD_001"."SEQ_AEA_ID"'),%s,%s)
    """

	keys = pd.read_sql_query(query_keys, db_connection)
	with db_connection.cursor() as cursor:
		for row in keys.itertuples():
			values = (row.ALR_ID, row.EXC_ID)
			cursor.execute(query_populate, values)


def populate_algo_currency_asso(db_connection, algo_names,
								currency_pairs: List):
	"""
	Writes cross product of algo_names and exchanges to table
	 "PROD_001"."ALGO_EXCHANGE_ASSOCIATION"
	"""

	if len(currency_pairs) == 1:
		currency_pairs.append(currency_pairs[0])
	if len(algo_names) == 1:
		algo_names.append(algo_names[0])

	algo_names, currency_pairs = tuple(algo_names), tuple(currency_pairs)

	query_keys = """
        SELECT
        	"ALR_ID",
        	"CUP_ID"
        FROM
        	"PROD_001"."ALGO_REGISTRY",
        	"PROD_001"."CURRENCY_PAIR"
        WHERE
        	"ALR_NAME" IN {}
        	AND "CUP_CODE" IN {}
    """.format(algo_names, currency_pairs)

	query_populate = """
        INSERT INTO "PROD_001"."ALGO_CURRENCY_ASSOCIATION"
        ("ACA_ID", "ACA_ALR_ID", "ACA_CUP_ID")
        VALUES (NEXTVAL('"PROD_001"."SEQ_ACA_ID"'),%s,%s)
    """

	keys = pd.read_sql_query(query_keys, db_connection)
	with db_connection.cursor() as cursor:
		for row in keys.itertuples():
			values = (row.ALR_ID, row.CUP_ID)
			cursor.execute(query_populate, values)


def create_schema_relations(db_connection):
	query = """
        --Create Schema, Tables and References
		--If you want to recreate and overwrite the existing schema, use the
		--following command: 
		--DROP SCHEMA IF EXISTS "PROD_001" CASCADE;
		CREATE SCHEMA IF NOT EXISTS "PROD_001";
		CREATE TABLE "PROD_001"."ALGO_REGISTRY" (
			"ALR_ID" INT PRIMARY KEY NOT NULL,
			"ALR_NAME" VARCHAR NOT NULL,
			"ALR_DESCRIPTION" VARCHAR NOT NULL,
			"ALR_STATUS" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."EXCHANGE" (
			"EXC_ID" INT PRIMARY KEY NOT NULL,
			"EXC_NAME" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."CURRENCY" (
			"CUR_ID" INT PRIMARY KEY NOT NULL,
			"CUR_CODE" VARCHAR NOT NULL,
			"CUR_TYPE" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."METRIC_DEFINITION" (
			"MED_ID" INT PRIMARY KEY NOT NULL,
			"MED_NAME" VARCHAR NOT NULL,
			"MED_DESCRIPTION" VARCHAR NOT NULL,
			"MED_CLASS_NAME" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."METRIC_CLASS_PARAMETER" (
			"MCP_ID" INT PRIMARY KEY NOT NULL,
			"MCP_MED_ID" INT REFERENCES "PROD_001"."METRIC_DEFINITION"("MED_ID") NOT NULL,
			"MCP_NAME" VARCHAR NOT NULL,
			"MCP_VALUE" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."ALGO_METRIC_ASSOCIATION" (
			"AMA_ID" INT PRIMARY KEY NOT NULL,
			"AMA_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"AMA_MED_ID" INT REFERENCES "PROD_001"."METRIC_DEFINITION"("MED_ID") NOT NULL
		);
		
		CREATE TABLE "PROD_001"."ALGO_CONFIGURATION" (
			"ALC_ID" INT PRIMARY KEY NOT NULL,
			"ALC_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"ALC_NAME" VARCHAR NOT NULL,
			"ALC_VALUE" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."ALGO_EXCHANGE_ASSOCIATION" (
			"AEA_ID" INT PRIMARY KEY NOT NULL,
			"AEA_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"AEA_EXC_ID" INT REFERENCES "PROD_001"."EXCHANGE"("EXC_ID") NOT NULL
		);
		
		CREATE TABLE "PROD_001"."CURRENCY_PAIR" (
			"CUP_ID" INT PRIMARY KEY NOT NULL,
			"CUP_CUR_ID_BASE" INT REFERENCES "PROD_001"."CURRENCY"("CUR_ID") NOT NULL,
			"CUP_CUR_ID_QUOTE" INT REFERENCES "PROD_001"."CURRENCY"("CUR_ID") NOT NULL,
			"CUP_CODE" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."ALGO_CURRENCY_ASSOCIATION" (
			"ACA_ID" INT PRIMARY KEY NOT NULL,
			"ACA_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"ACA_CUP_ID" INT REFERENCES "PROD_001"."CURRENCY_PAIR"("CUP_ID") NOT NULL
		);
		
		CREATE TABLE "PROD_001"."EXCHANGE_CURRENCY_PAIR" (
			"ECP_ID" INT PRIMARY KEY NOT NULL,
			"ECP_EXC_ID" INT REFERENCES "PROD_001"."EXCHANGE"("EXC_ID") NOT NULL,
			"ECP_CUP_ID" INT REFERENCES "PROD_001"."CURRENCY_PAIR"("CUP_ID") NOT NULL,
			"ECP_BASE_PREC" DOUBLE PRECISION,
			"ECP_QUOTE_PREC" DOUBLE PRECISION,
			"ECP_MIN_QTY" DOUBLE PRECISION,
			"ECP_STEPSIZE" DOUBLE PRECISION
		);
		
		CREATE TABLE "PROD_001"."BALANCE" (
			"BAL_ID" BIGINT PRIMARY KEY NOT NULL,
			"BAL_TIMESTAMP" TIMESTAMPTZ NOT NULL,
			"BAL_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"BAL_EXC_ID" INT REFERENCES "PROD_001"."EXCHANGE"("EXC_ID") NOT NULL,
			"BAL_CUR_ID" INT REFERENCES "PROD_001"."CURRENCY"("CUR_ID") NOT NULL,
			"BAL_AMOUNT" DOUBLE PRECISION NOT NULL,
			"BAL_QUOTE_PRICE" DOUBLE PRECISION NOT NULL,
			"BAL_QUOTE_CURRENCY" INT REFERENCES "PROD_001"."CURRENCY"("CUR_ID") NOT NULL
		);
		
		CREATE TABLE "PROD_001"."UNITS" (
			"UNI_ID" INT PRIMARY KEY NOT NULL,
			"UNI_SYMBOL" VARCHAR NOT NULL,
			"UNI_DESCRIPTION" VARCHAR
		);
		
		CREATE TABLE "PROD_001"."PERFORMANCE_LOG" (
		"PEL_ID" BIGINT PRIMARY KEY NOT NULL,
		"PEL_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
		"PEL_MED_ID" INT REFERENCES "PROD_001"."METRIC_DEFINITION"("MED_ID") NOT NULL,
		"PEL_UNI_ID" INT REFERENCES "PROD_001"."UNITS"("UNI_ID") NOT NULL,
		"PEL_TIMESTAMP" TIMESTAMPTZ NOT NULL,
		"PEL_VALUE" DOUBLE PRECISION NOT NULL,
		);
		
		CREATE TABLE "PROD_001"."ORDER_LOG" (
			"ORL_ID" UUID PRIMARY KEY NOT NULL,
			"ORL_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"ORL_EXC_ID" INT REFERENCES "PROD_001"."EXCHANGE"("EXC_ID") NOT NULL,
			"ORL_CUP_ID" INT REFERENCES "PROD_001"."CURRENCY_PAIR"("CUP_ID") NOT NULL,
			"ORL_COMBO_ID" VARCHAR,
			"ORL_TIMESTAMP" TIMESTAMPTZ NOT NULL,
			"ORL_QUANTITY" DOUBLE PRECISION NOT NULL,
			"ORL_PRICE"  DOUBLE PRECISION NOT NULL,
			"ORL_DIRECTION" VARCHAR NOT NULL,
			"ORL_TYPE" VARCHAR NOT NULL,
			"ORL_Q_FILLED" DOUBLE PRECISION NOT NULL,
			"ORL_STATUS" VARCHAR NOT NULL,
			"ORL_FEE"  DOUBLE PRECISION NOT NULL,
			"ORL_FEE_CURRENCY" INT REFERENCES "PROD_001"."CURRENCY"("CUR_ID") NOT NULL
		);
		
		CREATE TABLE "PROD_001"."SYSTEM_LOG" (
			"SYL_ID" BIGINT PRIMARY KEY NOT NULL,
			"SYL_ENTITY_NAME" VARCHAR NOT NULL,
			"SYL_ORL_ID" UUID,
			"SYL_TIMESTAMP" TIMESTAMPTZ NOT NULL,
			"SYL_LEVEL"  VARCHAR NOT NULL,
			"SYL_FILE" VARCHAR NOT NULL,
			"SYL_FUNCTION" VARCHAR NOT NULL,
			"SYL_LINE_NO" INT NOT NULL,
			"SYL_MESSAGE" VARCHAR NOT NULL
		);
		
		CREATE TABLE "PROD_001"."TRANSFERS" (
			"TRF_ID" BIGINT PRIMARY KEY NOT NULL,
			"TRF_ALR_ID" INT REFERENCES "PROD_001"."ALGO_REGISTRY"("ALR_ID") NOT NULL,
			"TRF_EXC_ID_IN" INT REFERENCES "PROD_001"."EXCHANGE"("EXC_ID") NOT NULL,
			"TRF_EXC_ID_OUT" INT REFERENCES "PROD_001"."EXCHANGE"("EXC_ID") NOT NULL,
			"TRF_CUR_ID" INT REFERENCES "PROD_001"."CURRENCY"("CUR_ID") NOT NULL,
			"TRF_TIMESTAMP" TIMESTAMPTZ NOT NULL,
			"TRF_AMOUNT" DOUBLE PRECISION NOT NULL
		);
		
		CREATE TABLE "PROD_001"."LATENCY_LOG" (
			"LAL_ID" BIGINT PRIMARY KEY NOT NULL,
			"LAL_TIMESTAMP" TIMESTAMPTZ NOT NULL,
			"LAL_TYPE" VARCHAR NOT NULL,
			"LAL_ORL_ID" UUID,
			"LAL_VALUE" INT
		);
		
		--Create Sequences
		CREATE SEQUENCE "PROD_001"."SEQ_ALR_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."ALGO_REGISTRY"."ALR_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_EXC_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."EXCHANGE"."EXC_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_CUR_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."CURRENCY"."CUR_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_MED_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."METRIC_DEFINITION"."MED_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_AMA_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."ALGO_METRIC_ASSOCIATION"."AMA_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_MCP_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."METRIC_CLASS_PARAMETER"."MCP_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_ALC_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."ALGO_CONFIGURATION"."ALC_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_AEA_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."ALGO_EXCHANGE_ASSOCIATION"."AEA_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_CUP_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."CURRENCY_PAIR"."CUP_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_ACA_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."ALGO_CURRENCY_ASSOCIATION"."ACA_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_ECP_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."EXCHANGE_CURRENCY_PAIR"."ECP_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_BAL_ID"
		AS BIGINT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."BALANCE"."BAL_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_PEL_ID"
		AS BIGINT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."PERFORMANCE_LOG"."PEL_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_SYL_ID"
		AS BIGINT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."SYSTEM_LOG"."SYL_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_TRF_ID"
		AS BIGINT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."TRANSFERS"."TRF_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_LAL_ID"
		AS BIGINT
		START 1
		INCREMENT 1
		OWNED BY "PROD_001"."LATENCY_LOG"."LAL_ID";
		
		CREATE SEQUENCE "PROD_001"."SEQ_UNI_ID"
		AS INT
		INCREMENT 1
		START 1
		OWNED BY "PROD_001"."UNITS"."UNI_ID";
    """
	with db_connection.cursor() as cursor:
		cursor.execute(query)
		print("SUCCESS: CREATE NEW SCHEMA")


############################### START SCRIPT ###################################


create_schema_relations(db_connector.connection)

alr = get_algo_registry(db_connector.connection)
lookup = migrate_algo_registry(db_connector.connection, alr)

alc = get_algo_config(db_connector.connection)
migrate_algo_config(db_connector.connection, alc, lookup)

cur = get_currency(db_connector.connection)
migrate_currency(db_connector.connection, cur)

exc = get_exchanges(db_connector.connection)
migrate_exchanges(db_connector.connection, exc)

cup = get_pairs(db_connector.connection)
populate_pairs(db_connector.connection, pairs)

populate_exchange_currency_pair(
	db_connector.connection, exchange_names, currency_pairs
)

populate_algo_exchange_asso(db_connector.connection, algos, algo_exchanges)
populate_algo_currency_asso(db_connector.connection, algos, cups_algo)

print("SUCCESS: POPULATE NEW SCHEMA")

if __name__ == '__main__':
	pass
