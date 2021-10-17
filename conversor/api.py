import os
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://test:test@db/test'
db = SQLAlchemy(app)
ma = Marshmallow(app)
app.config["JWT_SECRET_KEY"] = "cloud-conversor-jwt"
app.config['UPLOAD_PATH'] = '/files/uploads'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

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
        if request.get_json() is None:
            return {"error": "No request provided."}, 400

        if request.json['password1'] != request.json['password2']:
            return {"error": "password1 and password2 are not equal."}, 400

        new_user = User(
            username = request.json['username'],
            password = request.json['password1'],
            email = request.json['email']
        )
        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "User already exists."}, 409

        return user_schema.dump(new_user)

class AuthLoginResource(Resource):
    def post(self):
        if request.get_json() is None:
            return {"error": "No request provided."}, 400

        user = User.query.filter(User.username == request.json["username"],
                                       User.password == request.json["password"]).first()
        db.session.commit()
        if user is None:
            return {"error": "User does not exist"}, 404
        else:
            token = create_access_token(identity=user.email)
            return {"success": "Successful login.", "token": token}

class HealthResource(Resource):
    def get(self):
        return {"status": "UP"}, 200

class TasksResource(Resource):
    @jwt_required()
    def get(self):
        """
        tasks = Task.query.all()
        db.session.commit()
        response = [task_schema.dump(t) for t in tasks]
        return jsonify(response)"""
        usuario=User.query.get_or_404(request.json["id_usuario"])
        db.session.commit()
        response = [task_schema.dump(t) for t in usuario.tasks]
        return jsonify(response)


    @jwt_required()
    def post(self):

        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        if uploaded_file.filename != '':
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))

        new_task = Task(
            filename = uploaded_file.filename,
            timestap = datetime.now(),
            status = 'uploaded',
            new_format = request.values["new_format"],
            usuario = request.values["id_usuario"]
        )
        db.session.add(new_task)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"error": "Task is already registered."}, 409

        return {"success": "Task was successfully created"}, 200

class TaskResource(Resource):
    @jwt_required()
    def get(self, id_task):
        task=Task.query.get_or_404(id_task)
        return task_schema.dump(task)

    @jwt_required()
    def put(self, id_task):
        task = Task.query.get_or_404(id_task, "Task not exists")
        '''
        if task.status == 'processed':
            # TODO: ELIMINAR ARCHIVO YA PROCESADO
            task.filename        
        '''
        task.new_format = request.json["newFormat"]
        task.status = 'uploaded'

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"Error": "Task not updated."}, 404

        return task_schema.dump(task)

    @jwt_required()
    def delete(self, id_task):
        task = Task.query.get_or_404(id_task, "Task not exists")
        if task is not None:
            db.session.delete(task)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return {"Error": "Task not deleted."}, 404
        else:
            return {"Error": "Task not found."}, 404

        return {"Success": "Task was successfully deleted"}, 200

class FileResource(Resource):
    @jwt_required()
    def get(self):
        try:
            path_to_file = "ciletoMP3.mp3"

            return send_file(
                path_to_file,
                mimetype="audio/mp3",
                as_attachment=True,
                attachment_filename="ciletoMP3.mp3")
        except Exception as e:
            return str(e)


api.add_resource(HealthResource, '/api/auth/check')
api.add_resource(AuthSignupResource, '/api/auth/signup')
api.add_resource(AuthLoginResource, '/api/auth/login')
api.add_resource(TasksResource, '/api/tasks')
api.add_resource(TaskResource, '/api/tasks/<int:id_task>')
api.add_resource(FileResource, '/api/files')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', ssl_context='adhoc')

