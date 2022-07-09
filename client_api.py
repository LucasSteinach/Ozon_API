from flask import Flask, request
from pprint import pprint
from flask_restful import Api, Resource, reqparse
app = Flask(__name__)
api = Api(app)

# headers_args = reqparse.RequestParser()
# headers_args.add_argument('client_id', type=str, help='Input id for Ozon API')
# headers_args.add_argument('api_key', type=str, help='Input api_key for Ozon API')


class MarkActionsAPI(Resource):

    def __init__(self, connection):
        self.conn = connection

    def get(self, client_id):
        api.add_resource(MarkActionsAPI, '/mark_actions_api/<string:client_id>')
        cursor = self.conn.cursor().execute("SELECT * FROM mark_actions WHERE client_id_api = '" + client_id +"'")
        print("SELECT * FROM mark_actions WHERE client_id_api = '" + client_id +"'")
        # records = cursor.fetchall()
        # pprint(records)
        return cursor




if __name__ == '__main__':
    app.run(debug=True)
