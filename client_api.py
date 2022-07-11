from flask import Flask, request
from pprint import pprint
from ozon_api_connector import sql_connection, sql_my_auth_data
import psycopg2
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)

class MarkActionsAPI(Resource):

    def get(self, client_id_api):
        connect = sql_connection(*sql_my_auth_data)
        with connect.cursor() as pointer:
            pointer.execute("SELECT * FROM mark_actions WHERE client_id_api = '" + client_id_api + "'")
            records = pointer.fetchall()
        return records


api.add_resource(MarkActionsAPI,  '/mark_actions_api/<string:client_id_api>')


if __name__ == '__main__':
    app.run(debug=True)
