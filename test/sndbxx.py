import src.helpers
import src.util

logger_wrapper = src.util.LoggerWrapper(entity_name=1, location="log/test_file.log")
db_connector = src.helpers.DBConnector(logger_wrapper.logger, mode="TEST")

base_code, quote_code = "BTC", "USDT"

with db_connector.connection.cursor() as cur:
	query = f"""
	        SELECT
	            *
	        FROM "PROD_001"."CURRENCY_PAIR"
	        JOIN "PROD_001"."CURRENCY" AS "C_BASE"
	        ON "C_BASE"."CUR_ID" = "CUP_CUR_ID_BASE"
	        JOIN "PROD_001"."CURRENCY" AS "C_QUOTE"
	        ON "C_QUOTE"."CUR_ID" = "CUP_CUR_ID_QUOTE"
	           --AND "C_BASE"."CUR_CODE" = {base_code}
	            --AND "C_QUOTE"."CUR_CODE" = {quote_code}
	        	AND "C_BASE"."CUR_CODE" = '{base_code}'
	        	AND "C_QUOTE"."CUR_CODE" = '{quote_code}'
	    """
	cur.execute(query)
	print(cur.fetchall())