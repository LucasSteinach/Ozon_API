from psycopg2.extras import Json
from psycopg2.extensions import register_adapter
from ozon_api_connector import sql_connection, sql_my_auth_data

register_adapter(dict, Json)


if __name__ == '__main__':
    with sql_connection(*sql_my_auth_data) as connect:
        cursor = connect.cursor()
        cursor.execute("SELECT * FROM rules")
        data = cursor.fetchall()
    print(data)