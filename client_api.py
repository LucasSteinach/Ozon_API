from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)


class MarkActionsAPI(Resource):
    def get(self):
        return {'data': 'get'}

    def post(self):
        return {'data': 'post'}

    def delete(self):
        return {'data': 'delete'}

    def put(self):
        return {'data': 'put'}


api.add_resource(MarkActionsAPI, '/mark_actions_api')

if __name__ == '__main__':
    app.run(debug=True)