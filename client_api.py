import json.decoder

from flask import Flask, request
from pprint import pprint
from ozon_api_connector import sql_connection, sql_my_auth_data
import psycopg2.extras
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)


get_args = reqparse.RequestParser()
get_args.add_argument(name='client_id_api', type=str, help='correct client_id_api is required', required=True)

post_args = reqparse.RequestParser()
post_args.add_argument(name='client_id_api', type=str, help='correct client_id_api is required', required=True)
post_args.add_argument(name='rule', type=dict, help='Type of rule must be "dict"', required=True)

class MarkActionsAPI(Resource):

    # returns available to action products for client_id ordered descending by % discount
    def get(self):
        args = get_args.parse_args()
        with sql_connection(*sql_my_auth_data) as connect:
            pointer = connect.cursor()
            pointer.execute(f"""SELECT id_action, id_product, ROUND((1-max_action_price/price)*100) AS discount FROM 
            mark_actions WHERE client_id_api = '{args['client_id_api']}' AND action_price = 0 ORDER BY discount DESC""")
            records = pointer.fetchall()
            result = {'data': []}
            for product in records:
                result['data'].append({
                    'id_action': product[0],
                    'id_product': product[1],
                    'discount': product[2]
                })
        return result

    # adds goods to action
    def put(self):
        req_data = get_args.parse_args()
        print(req_data)
        return '', 201

    # stores rules in db
    def post(self):
        args = post_args.parse_args()
        with sql_connection(*sql_my_auth_data) as connect:
            pointer = connect.cursor()
            pointer.execute(f"""CREATE TABLE IF NOT EXISTS rules (
                id SERIAL PRIMARY KEY,
                client_id_api VARCHAR(40) NOT NULL,
                rule jsonb
            )""")
            pointer.execute(f"""INSERT INTO rules (client_id_api, rule) 
                VALUES ({args['client_id_api']},
                {args['rule']}
            )""")

        return

    # deletes good from action
    def delete(self):
        return


api.add_resource(MarkActionsAPI, '/mark_actions_api')


if __name__ == '__main__':
    app.run(debug=True)
