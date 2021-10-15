from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://test:test@db/test'
db = SQLAlchemy(app)
ma = Marshmallow(app)
app.config["JWT_SECRET_KEY"] = "cloud-conversor-jwt"

jwt = JWTManager(app)
api = Api(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    timestap = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    new_format = db.Column(db.String(50))
    usuario = db.Column(db.Integer, db.ForeignKey("user.id"))

class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ("id", "filename", "timestap","status","new_format")
task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)
    tasks = db.relationship('Task', cascade='all, delete, delete-orphan')


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ("id", "username", "email")

user_schema = UserSchema()
users_schema = UserSchema(many=True)

class AuthSignupResource(Resource):
    def post(self):
        new_user = User(
            username = request.json['username'],
            password = request.json['password1'],
            email = request.json['email']
        )
        db.session.add(new_user)
        db.session.commit()
        return user_schema.dump(new_user)

class AuthLoginResource(Resource):
    def post(self):
        user = User.query.filter(User.username == request.json["username"],
                                       User.password == request.json["password"]).first()
        db.session.commit()
        if user is None:
            return "El usuario no existe", 404
        else:
            token = create_access_token(identity=user.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": token}

class HealthResource(Resource):
    def get(self):
        return {"status": "UP"}, 200

class TasksResource(Resource):
    @jwt_required()
    def get(self):
        return {"status": "ok"}, 200

    def post(self):
        return {"status": "ok"}, 200

class TaskResource(Resource):
    def get(self, id_task):
        return {"status": "ok"}, 200

    def put(self, id_task):
        return {"status": "ok"}, 200

    def delete(self, id_task):
        return {"status": "ok"}, 200

class FileResource(Resource):
    def get(self, file):
        return {"status": "ok"}, 200

api.add_resource(HealthResource, '/api/auth/check')
api.add_resource(AuthSignupResource, '/api/auth/signup')
api.add_resource(AuthLoginResource, '/api/auth/login')
api.add_resource(TasksResource, '/api/tasks')
api.add_resource(TaskResource, '/api/tasks/<int:id_task>')
api.add_resource(FileResource, '/api/files')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', ssl_context='adhoc')

