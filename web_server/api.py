import os
import random
from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from werkzeug.utils import secure_filename
import smtplib, ssl
from datetime import timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = str(os.environ.get('SQLALCHEMY_DATABASE_URI'))
db = SQLAlchemy(app, engine_options={"pool_size": 65})
ma = Marshmallow(app)
app.config["JWT_SECRET_KEY"] = "cloud-coversor-jwt"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=6)
app.config['UPLOAD_PATH'] = '/files'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

jwt = JWTManager(app)
api = Api(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime)
    status = db.Column(db.String(50))
    new_format = db.Column(db.String(50))
    format = db.Column(db.String(50))
    origin_path = db.Column(db.String(50))
    convert_path = db.Column(db.String(50))
    usuario = db.Column(db.Integer, db.ForeignKey("user.id"))
    timeProces = db.Column(db.Integer)

class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        fields = ("id", "filename", "timestamp", "status", "new_format", "format", "origin_path", "convert_path", "timeProces")


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
            username=request.json['username'],
            password=request.json['password1'],
            email=request.json['email']
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
        if request.get_json() is None:
            return {"error": "No request provided."}, 400
        usuario = User.query.get_or_404(request.json["id_usuario"])
        db.session.commit()
        response = [task_schema.dump(t) for t in usuario.tasks]
        return jsonify(response)

    @jwt_required()
    def post(self):

        uploaded_file = request.files['file']
        filename = secure_filename(uploaded_file.filename)
        timestampName = datetime.now().strftime("%Y%m%d%H%M%S")
        ramdom_name_id = str(random.randint(0,22))
        name = os.path.splitext(filename)[0] + \
                       ((timestampName[:12]) if len(timestampName) < 12 else timestampName) + os.path.splitext(filename)[1]
        origin_path = app.config['UPLOAD_PATH'] + "/" + ramdom_name_id + name


        if uploaded_file.filename != '':
            uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'],ramdom_name_id +  name))

        new_task = Task(
            filename=uploaded_file.filename,
            format=uploaded_file.content_type,
            origin_path=origin_path,
            timestamp=datetime.now(),
            status='uploaded',
            new_format=request.values["new_format"],
            usuario=request.values["id_usuario"]
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
        task = Task.query.get_or_404(id_task)
        return task_schema.dump(task)

    @jwt_required()
    def put(self, id_task):
        if request.get_json() is None:
            return {"error": "No request provided."}, 400
        task = Task.query.get_or_404(id_task, "Task not exists")

        if task.status == 'processed':
            if os.path.exists(task.convert_path):
                os.remove(task.convert_path)

        task.new_format = request.json["newFormat"]
        task.timeProces = 0
        task.convert_path = ''
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


class Convert:

    def convert_generic(self, orig_song, dest_song):
        os.system('ffmpeg -loglevel %s -i \"%s\"  \"%s\"' % ('fatal', orig_song, dest_song))

    def convert_mp3_to_wav(self, orig_song, dest_song):
        song = AudioSegment.from_mp3(orig_song)
        song.export(dest_song, format="wav")

    def convert_mp3_to_wma(self, orig_song, dest_song):
        os.system('ffmpeg -loglevel %s -i \"%s\" -acodec libmp3lame \"%s\"' % ('fatal', orig_song, dest_song))

    def convert_mp3_to_ogg(self, orig_song, dest_song):
        song = AudioSegment.from_mp3(orig_song)
        song.export(dest_song, format="ogg")        

    # OGG Files
    def convert_ogg_to_wav(self, orig_song, dest_song):
        song = AudioSegment.from_ogg(orig_song)
        song.export(dest_song, format="wav")

    def convert_ogg_to_mp3(self, orig_song, dest_song):
        song = AudioSegment.from_ogg(orig_song)
        song.export(dest_song, format="mp3")

    # WAV Files
    def convert_wav_to_mp3(self, orig_song, dest_song):
        song = AudioSegment.from_wav(orig_song)
        song.export(dest_song, format="mp3")

    def convert_wav_to_ogg(self, orig_song, dest_song):
        song = AudioSegment.from_wav(orig_song)
        song.export(dest_song, format="ogg")

    def convert_wav_to_ogg(self, orig_song, dest_song):
        song = AudioSegment.from_wav(orig_song)
        song.export(dest_song, format="ogg")


# MP3 - ACC - OGG - WAV – WMA


class FileResource(Resource):
    @jwt_required()
    def get(self, id_task):
        try:
            task = Task.query.get_or_404(id_task)
            if task.status == 'uploaded':
                path_to_file = task.origin_path
                format = task.format
            else:
                path_to_file = task.convert_path
                format = task.new_format

            return send_file(
                path_to_file,
                mimetype="audio/" + format,
                as_attachment=True,
                attachment_filename=os.path.splitext(task.filename)[0]+ "." + format)
        except Exception as e:
            return str(e)


class EmailSend:

    def send(self, receiver_email):
        port = 465  # For SSL
        password = "contrasena2021"
        sender_email = "micorreonube2021@gmail.com"
        message = """\
        Subject: Cloud Conversion Tool Update

        We hope this message finds you well, your File was succesfully converted. Thanks for using the Cloud conversion tool"""

        # Send email here
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)


api.add_resource(HealthResource, '/api/auth/check')
api.add_resource(AuthSignupResource, '/api/auth/signup')
api.add_resource(AuthLoginResource, '/api/auth/login')
api.add_resource(TasksResource, '/api/tasks')
api.add_resource(TaskResource, '/api/task/<int:id_task>')
api.add_resource(FileResource, '/api/files/<int:id_task>')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', ssl_context='adhoc', threaded=True)
