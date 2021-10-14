from flask import Flask, request

app = Flask(__name__)
api = Api(app)

class AuthSignupResource(Resource):
    def post(self):
        request.json['username']
        request.json['password1']
        request.json['password2']
        request.json['email']

class AuthLoginResource(Resource):
    def post(self):

class TaskResource(Resource):
    def get(self):

    def post(self):

    def get(self, id_task):

    def put(self, id_task):

    def delete(self, id_task):

class FileResource():
    def get(self, file):

api.add_resource(AuthSignupResource, '/api/auth/signup')
api.add_resource(AuthLoginResource, '/api/auth/login')
api.add_resource(TaskResource, '/api/tasks')
api.add_resource(FileResource, '/api/files')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')