#!/usr/bin/python3
# -*- coding: utf-8 -*-

import uuid
import src.helpers
import quant_sdk


def query_algo_configuration(algo_name):
    return f"""
        SELECT
            "ALC_ALR_ID",
            "ALC_NAME",
            "ALC_VALUE"
        FROM
            "PROD_001"."ALGO_REGISTRY",
            "PROD_001"."ALGO_CONFIGURATION"
        WHERE
            "ALR_ID" = "ALC_ALR_ID"
            AND "ALR_NAME" = '{algo_name}'
    """


def query_algo_id(algo_name):
    return f"""
        SELECT
            ar."ALR_ID"
        FROM
            "PROD_001"."ALGO_REGISTRY" ar
        WHERE
            ar."ALR_NAME" = '{algo_name}'
    """


def query_currency_pairs():
    return """
        SELECT
            "CUP_ID",
            "C_BASE"."CUR_CODE",
            "C_QUOTE"."CUR_CODE",
            "CUP_CODE"
        FROM "PROD_001"."CURRENCY_PAIR"
        JOIN "PROD_001"."CURRENCY" AS "C_BASE"
        ON "C_BASE"."CUR_ID" = "CUP_CUR_ID_BASE"
        JOIN "PROD_001"."CURRENCY" AS "C_QUOTE"
        ON "C_QUOTE"."CUR_ID" = "CUP_CUR_ID_QUOTE"
    """


def query_algo_specific_currency_pairs(algo_name):
    return f"""
        SELECT
            "CUP_ID",
            "C_BASE"."CUR_ID",
            "C_BASE"."CUR_CODE",
            "C_QUOTE"."CUR_ID",
            "C_QUOTE"."CUR_CODE",
            "CUP_CODE"
        FROM "PROD_001"."CURRENCY_PAIR"
        JOIN "PROD_001"."ALGO_CURRENCY_ASSOCIATION"
        ON "ACA_CUP_ID" = "CUP_ID"
        JOIN "PROD_001"."ALGO_REGISTRY"
        ON "ACA_ALR_ID" = "ALR_ID"
        JOIN "PROD_001"."CURRENCY" AS "C_BASE"
        ON "C_BASE"."CUR_ID" = "CUP_CUR_ID_BASE"
        JOIN "PROD_001"."CURRENCY" AS "C_QUOTE"
        ON "C_QUOTE"."CUR_ID" = "CUP_CUR_ID_QUOTE"
        WHERE "ALR_NAME" = '{algo_name}'
    """


def query_currency_pair_id(base_code, quote_code):
    return f"""
        SELECT
            "CUP_ID"
        FROM "PROD_001"."CURRENCY_PAIR"
        JOIN "PROD_001"."CURRENCY" AS "C_BASE"
        ON "C_BASE"."CUR_ID" = "CUP_CUR_ID_BASE"
        JOIN "PROD_001"."CURRENCY" AS "C_QUOTE"
        ON "C_QUOTE"."CUR_ID" = "CUP_CUR_ID_QUOTE"
            AND "C_BASE"."CUR_CODE" = '{base_code}'
            AND "C_QUOTE"."CUR_CODE" = '{quote_code}'
    """


def query_currency_id(currency_code):
    return f"""
        SELECT "CUR_ID"
        FROM "PROD_001"."CURRENCY"
        WHERE "CUR_CODE" = '{currency_code}'
    """


def query_algo_exchange_association(algo_name):
    return f"""
        SELECT
        "EXC_ID",
        "EXC_NAME"
        FROM "PROD_001"."EXCHANGE"
        JOIN "PROD_001"."ALGO_EXCHANGE_ASSOCIATION"
        ON "AEA_EXC_ID" = "EXC_ID"
        JOIN "PROD_001"."ALGO_REGISTRY"
        ON "AEA_ALR_ID" = "ALR_ID"
        WHERE "ALR_NAME" = '{algo_name}'
    """


def query_exchange_currency_pairs(algo_name, exchange_id):
    return f"""
        SELECT
            "CUP_ID",
            "C_BASE"."CUR_CODE",
            "C_QUOTE"."CUR_CODE",
            "CUP_CODE"
        FROM "PROD_001"."CURRENCY_PAIR"
        JOIN "PROD_001"."ALGO_CURRENCY_ASSOCIATION"
        ON "ACA_CUP_ID" = "CUP_ID"
        JOIN "PROD_001"."ALGO_REGISTRY"
        ON "ACA_ALR_ID" = "ALR_ID"
        JOIN "PROD_001"."CURRENCY" AS "C_BASE"
        ON "C_BASE"."CUR_ID" = "CUP_CUR_ID_BASE"
        JOIN "PROD_001"."CURRENCY" AS "C_QUOTE"
        ON "C_QUOTE"."CUR_ID" = "CUP_CUR_ID_QUOTE"
        JOIN "PROD_001"."EXCHANGE_CURRENCY_PAIR"
        ON "ECP_CUP_ID" = "CUP_ID"
        WHERE "ALR_NAME" = '{algo_name}'
            AND "ECP_EXC_ID" = {exchange_id}
    """


def select_order_log_closed_orders(start_time, end_time, algorithm_id):
    return f"""
    SELECT 
        * 
    FROM 
        "PROD_001"."ORDER_LOG" 
    WHERE
        "ORL_ALR_ID" = {algorithm_id} AND 
        "ORL_STATUS" = 'CLOSED' AND
        "ORL_TIMESTAMP"
            BETWEEN 
                '{start_time}'
                AND '{end_time}'
    ORDER BY "ORL_TIMESTAMP" ASC
    """


def insert_into_order_log(algo_id, exchange_id, order_response, logger):
    base = order_response["order"]["base_currency"]
    quote = order_response["order"]["quote_currency"]
    # Format timestamp compatible with PostgreSQL DB
    timestamp_ = order_response['order']['order_timestamp']
    timestamp_ = src.helpers.convert_timestamp_to_datetime(
        timestamp_, logger
    )
    order_response['order']['order_timestamp'] = timestamp_
    return f"""
        INSERT INTO "PROD_001"."ORDER_LOG" (
            "ORL_ID", "ORL_ALR_ID", "ORL_EXC_ID", "ORL_CUP_ID", "ORL_COMBO_ID",
            "ORL_TIMESTAMP", "ORL_QUANTITY", "ORL_PRICE", "ORL_DIRECTION", 
            "ORL_TYPE", "ORL_Q_FILLED", "ORL_STATUS", "ORL_FEE",
            "ORL_FEE_CURRENCY"
        )
        VALUES (
            '{order_response['order']['order_id']}',
            '{algo_id}',
            '{exchange_id}',
            ({query_currency_pair_id(base, quote)}),
            '{uuid.uuid4()}',
            '{order_response['order']['order_timestamp']}',
            {order_response['order']['quantity']},
            '{order_response['order']['limit_price']}',
            '{order_response['order']['direction']}',
            '{order_response['order']['type']}',
            '{order_response['trade_status'][0]['trade']['trade_quantity']}',
            '{quant_sdk.Client.parse_order_status_code(order_response['aggregated_status'])}',
            '{order_response['trade_status'][0]['status_report']['fees']}',
            ({query_currency_id(order_response['trade_status'][0]['status_report']['fee_currency'])})
        )
    """


def update_order_log(order_id, price_executed, filled_quantity,
                     status, fee, fee_currency_code):
    return f"""
        UPDATE "PROD_001"."ORDER_LOG"
        SET "ORL_PRICE" = {price_executed},
            "ORL_Q_FILLED" = {filled_quantity},
            "ORL_STATUS" = '{status}',
            "ORL_FEE" = {fee},
            "ORL_FEE_CURRENCY" = ({query_currency_id(fee_currency_code)})
        WHERE "ORL_ID" = '{order_id}'
    """


def error_log_to_db():
    return """
        INSERT INTO "PROD_001"."SYSTEM_LOG"
            ("SYL_ID", "SYL_ENTITY_NAME", "SYL_ORL_ID", "SYL_TIMESTAMP", "SYL_LEVEL",
            "SYL_FILE", "SYL_FUNCTION", "SYL_LINE_NO", "SYL_MESSAGE")
        VALUES
            (NEXTVAL('"PROD_001"."SEQ_SYL_ID"'), %s, %s, %s, %s, %s, %s, %s, %s)
    """


def select_all_algorithms_with_status(status):
    return f"""
    SELECT 
        * 
    FROM 
        "PROD_001"."ALGO_REGISTRY" ar 
    WHERE 
        ar."ALR_STATUS" = '{status}'
    """


def select_id_of_unit_by_symbol(symbol):
    return f"""
    SELECT 
        "UNI_ID"
    FROM
        "PROD_001"."UNITS" u
    WHERE
        u."UNI_SYMBOL" = '{symbol}'
    """


# TODO adapt to sub-account / algorithm related balances
def insert_into_balances(logger, **kwargs):
    # Format timestamp compatible with PostgreSQL DB
    timestamp_ = kwargs['order']['order_timestamp']
    timestamp_ = src.helpers.convert_timestamp_to_datetime(
        timestamp_, logger
    )
    kwargs['order']['order_timestamp'] = timestamp_
    return f"""
        INSERT INTO "PROD_001"."BALANCE" ()
        VALUES (
            NEXTVAL('"PROD_001"."SEQ_BAL_ID'), {kwargs['timestamp']},
            '{kwargs['currency']}', {kwargs['amount']}, '{kwargs['exchange']}', 
            {kwargs['quote_price']}, '{kwargs['quote_currency']}'
        )
    """


def query_log_latency():
    return """
        INSERT INTO "PROD_001"."LATENCY_LOG"
            ("LAL_ID", "LAL_TIMESTAMP", "LAL_TYPE", "LAL_ORL_ID", "LAL_VALUE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_LAL_ID"'),%s,%s,%s,%s)
    """


def select_from_metric_related_algorithm_from_metric_definition(algorithm):
    return f"""
    SELECT 
        md."MED_ID", 
        md."MED_NAME", 
        md."MED_DESCRIPTION", 
        md."MED_CLASS_NAME" 
    FROM 
        "PROD_001"."ALGO_REGISTRY" ar, 
        "PROD_001"."ALGO_METRIC_ASSOCIATION" ama, 
        "PROD_001"."METRIC_DEFINITION" md 
    WHERE 
        ar."ALR_NAME" = '{algorithm}' 
        AND ama."AMA_ALR_ID" = ar."ALR_ID" 
        AND ama."AMA_MED_ID" = ar."ALR_ID"   
    """


def insert_into_metric(timestamp, metric_id, value, algorithm_id, unit_id):
    return f"""
    INSERT INTO
        "PROD_001"."PERFORMANCE_LOG"
     VALUES (
        (SELECT NEXTVAL('"PROD_001"."SEQ_PEL_ID"')),
        {algorithm_id}, 
        {metric_id}, 
        {unit_id},
        '{timestamp}', 
        {value})
    """


def select_configuration_of_metric(metric_id):
    return f"""
    SELECT 
        * 
    FROM 
        "PROD_001"."METRIC_CLASS_PARAMETER" mc
    WHERE 
        mc."MCP_MED_ID" = {metric_id}
    """


def select_last_balance():
    return """
    SELECT 
        * 
    FROM 
        balances 
    WHERE 
        timestamp = (SELECT (MAX(timestamp)) from balances)
    """


######################### INSERTS INTO INFO TABLES ##########################

def query_insert_currency():
    return """
        INSERT INTO "PROD_001"."CURRENCY"
        ("CUR_ID", "CUR_CODE", "CUR_TYPE")
        VALUES (NEXTVAL('"PROD_001"."SEQ_CUR_ID"'),%s,%s)
    """
