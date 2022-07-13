from flask import Flask, request
from pprint import pprint
from ozon_api_connector import sql_connection, sql_my_auth_data
import psycopg2
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)

get_args = reqparse.RequestParser()
get_args.add_argument(name='client_id_api', type=str, help='correct client_id_api is required', required=True)
get_args.add_argument(name='api_key', type=str, help='correct api_key is required', required=True)


class MarkActionsAPI(Resource):

    def get(self):
        req_data = get_args.parse_args()
        connect = sql_connection(*sql_my_auth_data)
        with connect.cursor() as pointer:
            pointer.execute(f"SELECT * FROM mark_actions WHERE client_id_api = '{req_data['client_id_api']}'")
            records = pointer.fetchall()
        return {req_data['client_id_api']: records}


api.add_resource(MarkActionsAPI,  '/mark_actions_api')


if __name__ == '__main__':
    app.run(debug=True)
