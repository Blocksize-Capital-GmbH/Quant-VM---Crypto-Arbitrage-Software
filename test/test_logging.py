import src.helpers
import src.util

# To test logging w/o db connection simply set the db in .env to invalid name
def test_logging_db():

    logger_wrapper = src.util.LoggerWrapper(entity_name=1, location="log/test_file.log")
    db_connector = src.helpers.DBConnector(logger_wrapper.logger, mode="DEV")
    print(db_connector._connection.closed, type(db_connector._connection.closed))
    if db_connector._connection is not None:
        print("SUCCESS: DB_Connection")

    logger_wrapper.db_connector = db_connector
    logger_wrapper.add_db_handler()
    logger_wrapper._logger.error("This is a test")
    db_connector._connection.close()
    print(db_connector._connection.closed)

test_logging_db()

