from flask import Flask
from ozon_api_connector import sql_connection, sql_my_auth_data
from flask_restful import Api, Resource, reqparse

app = Flask(__name__)
api = Api(app)


# sql_my_auth_data = (
# db_name: str,
# db_user: str,
# db_password: str,
# db_host: str,
# db_port: str,
# target_session_attrs: str,
# sslmode: str
# )

class MarkActionsAPI(Resource):

    # stores rules in db
    @staticmethod
    def put():
        put_args = reqparse.RequestParser()
        put_args.add_argument(name='api_id', type=str, help='correct api_id is required', required=True)
        put_args.add_argument(name='client_id', type=int, help='correct client_id is required', required=True)
        put_args.add_argument(name='rule', type=str, help='Type of rule must be str', required=True)
        args = put_args.parse_args()
        args['rule'] = args['rule'].replace("'", '"')
        with sql_connection(*sql_my_auth_data) as connect:
            pointer = connect.cursor()
            pointer.execute("SELECT COUNT(*) from mark_actions_rules_table")
            records_count = pointer.fetchall()[0][0] + 1
            pointer.execute(f"""INSERT INTO mark_actions_rules_table (id, api_id, client_id, rule)
                        VALUES ({records_count},
                        '{args['api_id']}',
                        {args['client_id']},
                        '{(args['rule'])}')
            """)
            pointer.execute("SELECT MAX(id) from mark_actions_rules_table")
            res = pointer.fetchall()[0][0]
        return f"New rule #{res} added", 201

    # get rules from db
    @staticmethod
    def post():
        post_args = reqparse.RequestParser()
        post_args.add_argument(name='api_id', type=str, help='correct client_id_api is required', required=True)
        post_args.add_argument(name='client_id', type=int, help='Type of rule must be "dict"', required=True)
        req_data = post_args.parse_args()
        with sql_connection(*sql_my_auth_data) as connect:
            cursor = connect.cursor()
            cursor.execute(f"""SELECT * FROM mark_actions_rules_table WHERE 
            api_id = '{req_data['api_id']}' AND client_id = {req_data['client_id']}""")
            res = {"rules": []}
            while True:
                record = cursor.fetchone()
                if not record:
                    break
                res["rules"].append({
                    'rule_id': record[0],
                    'api_id': record[1],
                    'rule_description': record[2],
                    'client_id': record[3]
                })
        return res, 200


class MarkActionsAPIProducts(Resource):
    # returns available to action products for client_id ordered descending by % discount
    @staticmethod
    def post():
        post_args = reqparse.RequestParser()
        post_args.add_argument(name='api_id', type=str, help='correct api_id is required', required=True)
        post_args.add_argument(name='discount', type=str, help='Correct discount is required', required=True)
        args = post_args.parse_args()
        with sql_connection(*sql_my_auth_data) as connect:
            pointer = connect.cursor()
            pointer.execute(f"""SELECT id, id_product, id_action, price, action_price, max_action_price, add_mode, 
                stock, min_stock, date_end::text, client_id_api, ROUND((1-max_action_price/price)*100) AS discount FROM 
                mark_actions WHERE client_id_api = '{args['api_id']}' AND action_price = 0 AND 
                ROUND((1-max_action_price/price)*100) <= {args['discount']} ORDER BY discount DESC """)
            records = pointer.fetchall()
            result = {'data': []}
            for product in records:
                result['data'].append({
                    'id': product[1],
                    'id_action': product[2],
                    'price': product[3],
                    'action_price': product[4],
                    'max_action_price': product[5],
                    'add_mode': product[6],
                    'stock': product[7],
                    'min_stock': product[8],
                    'date_end': product[9],
                    'client_id_api': product[10],
                    'discount': product[11]
                })
        return result


api.add_resource(MarkActionsAPI, '/mark_actions_api')
api.add_resource(MarkActionsAPIProducts, '/mark_actions_api/available_products')

if __name__ == '__main__':
    app.run(debug=True)
