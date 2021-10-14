from flask import Flask, request

app = Flask(__name__)
api = Api(app)


class TaskResource(Resource):
    def get(self):

    def post(self):

    def get(self, id_task):

    def put(self, id_task):

    def delete(self, id_task):

class FileResource():
    def get(self, file):


api.add_resource(TaskResource, '/api/tasks')
api.add_resource(FileResource, '/api/files')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')