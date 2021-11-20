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
from pydub import AudioSegment
import smtplib, ssl
from datetime import timedelta
import boto3
import botocore

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = str(os.environ.get('SQLALCHEMY_DATABASE_URI'))
db = SQLAlchemy(app)
ma = Marshmallow(app)
app.config["JWT_SECRET_KEY"] = "cloud-coversor-jwt"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=6)
app.config['UPLOAD_PATH'] = '/files'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

BUCKET = str(os.environ.get('BUCKET_NAME'))
AWS_ACCESS_KEY_ID = str(os.environ.get('AWS_ACCESS_KEY'))
AWS_SECRET_ACCESS_KEY = str(os.environ.get('AWS_SECRET_ACCESS'))
AWS_SESSION_TOKEN = str(os.environ.get('AWS_SESSION_TOKEN'))

jwt = JWTManager(app)
api = Api(app)


def download_file(file_name, bucket):
    object_name = file_name
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             aws_session_token=AWS_SESSION_TOKEN)
    with open(file_name, 'wb') as f:
        s3_client.download_fileobj(bucket, object_name, f)

def upload_file(file_name, bucket):
    object_name = file_name
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             aws_session_token=AWS_SESSION_TOKEN)
    response = s3_client.upload_file(file_name, bucket, object_name)
    return response

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


class HealthResource(Resource):
    def get(self):
        return {"status": "UP"}, 200


class ProcessTask(Resource):

    def get(self):
        download_file(request.json["origin_path"], BUCKET)
        return {"status": "downloaded"}, 200

    def post(self):
        tasks = db.session.query(Task).filter(Task.status == 'uploaded').all()
        for task in tasks:
            convert = Convert()
            timestampName = datetime.now().strftime("%Y%m%d%H%M%S")
            convert_path = app.config['UPLOAD_PATH'] + "/" + str(random.randint(0,100)) + os.path.splitext(task.filename)[0] + \
                           ((timestampName[:10]) if len(timestampName) < 10 else timestampName) + "." + task.new_format
            timestampBegin = datetime.now()
            ## descargar archivo original para procesar
            try:
                download_file(task.origin_path, BUCKET)
            except botocore.exceptions.ClientError as error:
                raise error

            if task.format == "mp3" and task.new_format == "ogg":
                convert.convert_mp3_to_ogg(task.origin_path, convert_path)
            else:            
                convert.convert_generic(task.origin_path, convert_path) 

            ## subir a S3 el archivo procesado al nuevo formato
            upload_file(convert_path, BUCKET)

            task.convert_path = convert_path
            timestampEnd = datetime.now()
            diff = timestampEnd - timestampBegin
            task.timeProces = int(diff.total_seconds() * 1000) # milliseconds
            task.status = 'processed'
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                return {"error": "Task is already registered."}, 409
            os.remove(task.origin_path)
            os.remove(convert_path)
            
            #if request is not None and request.json["send_email"] is not None:
            #enviar = EmailSend()
            #enviar.send("stationfile@gmail.com")
        response = [task_schema.dump(t) for t in tasks]
        return jsonify(response)


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
api.add_resource(ProcessTask, '/api/process')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', ssl_context='adhoc', threaded=True)
