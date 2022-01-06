import src.helpers
import src.util.util
import src.sql_queries

import pandas as pd

logger_wrapper = src.util.LoggerWrapper(1)
db_connector = src.helpers.DBConnector(logger_wrapper)

query = """
    SELECT "SYL_TIMESTAMP"
    FROM "PROD_001"."SYSTEM_LOG"
    ORDER BY "SYL_TIMESTAMP" DESC
    LIMIT 1
"""

datetime = pd.read_sql_query(query, db_connector.connection).iloc[0, 0]
print(datetime)
print(
    datetime, src.helpers.convert_datetime_to_unix(
            datetime
        )
)

