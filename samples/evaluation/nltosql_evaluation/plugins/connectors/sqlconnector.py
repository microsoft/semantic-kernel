import pyodbc
import time

from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
)
from semantic_kernel.orchestration.sk_context import SKContext


class SQLConnection:
    connection_string = ""
    connection = None

    def get_connection(connection_string: str):
        if connection_string != SQLConnection.connection_string:
            SQLConnection.connection_string = connection_string
            # print("[SQLConnection,get_connection()] - SQL Server connection string is changed -> ", connection_string)

        if SQLConnection.connection == None:
            SQLConnection.connection = pyodbc.connect(connection_string)
            # print("[SQLConnection,get_connection()] - SQL Server is connected to ", connection_string)
        # else:
        # print("[SQLConnection,get_connection()] - ", SQLConnection.connection_string)

        return SQLConnection.connection

    def create_connection_string(context: SKContext):
        server = context["sql_server_name"]
        database = context["sql_server_database_name"]
        username = context["sql_server_username"]
        password = context["sql_server_password"]
        driver = context["sql_server_odbc_driver"]

        return f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

    @sk_function(description="Check SQL syntax", name="check_sql_syntax")
    def check_sql_syntax(self, context: SKContext) -> str:
        connection_string = SQLConnection.create_connection_string(context=context)
        sql = context["sql"]

        try:
            connection = SQLConnection.get_connection(
                connection_string=connection_string
            )
            cursor = connection.cursor()

            cursor.execute(sql)
            cursor.close()
            print("SQL query is valid.")
            return "True"
        except pyodbc.Error as e:
            print("SQL query is invalid ->", str(e))
            context["sql_error"] = str(e)
            return "False"

    @sk_function(description="Check SQL syntax", name="execute")
    def execute(self, context: SKContext) -> str:
        connection_string = SQLConnection.create_connection_string(context=context)
        sql = context["sql"]

        executed = "True"

        try:
            connection = SQLConnection.get_connection(
                connection_string=connection_string
            )
            cursor = connection.cursor()

            # print("[SQLConnection,execute()] - ", sql)
            # elapsed time starts..
            start_time = time.time()

            # execute query..
            cursor.execute(sql)

            # measure elapsed time..
            context["elapsed_time"] = time.time() - start_time

            result_set = cursor.fetchall()
            cursor.close()

            # print("[SQLConnection,execute()] result_set count=", len(result_set))
            context["result_set"] = result_set
        except pyodbc.Error as e:
            # print("[SQLConnection,execute()] error in executing SQL:", str(e))
            context["sql_error"] = str(e)
            executed = "False"

        return executed
