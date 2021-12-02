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
app.config['UPLOAD_PATH'] = './'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

BUCKET = str(os.environ.get('BUCKET_NAME'))
AWS_ACCESS_KEY_ID = str(os.environ.get('AWS_ACCESS_KEY'))
AWS_SECRET_ACCESS_KEY = str(os.environ.get('AWS_SECRET_ACCESS'))
AWS_SESSION_TOKEN = str(os.environ.get('AWS_SESSION_TOKEN'))
REGION_NAME = str(os.environ.get('REGION_NAME'))
QUEUE_NAME = str(os.environ.get('QUEUE_NAME'))
QUEUE_URL = str(os.environ.get('QUEUE_URL'))

## Class models
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

## Functions ##

## get file from S3
def download_file(file_name, bucket):
    object_name = file_name
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             aws_session_token=AWS_SESSION_TOKEN)
    with open(file_name, 'wb') as f:
        s3_client.download_fileobj(bucket, object_name, f)

## Send file to S3
def upload_file(file_name, bucket):
    object_name = file_name
    s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                             aws_session_token=AWS_SESSION_TOKEN)
    response = s3_client.upload_file(file_name, bucket, object_name)
    return response

## Get message from SQS 
def receive_message():
    sqs = boto3.client('sqs', region_name=REGION_NAME,
                    aws_access_key_id=AWS_ACCESS_KEY_ID, 
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    aws_session_token=AWS_SESSION_TOKEN)

    response = sqs.receive_message(
        QueueUrl=QUEUE_URL,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=30,
        WaitTimeSeconds=0
    )
    message = response['Messages'][0]
    return message

## Delete message on SQS
def delete_message(message):
    sqs = boto3.client('sqs', region_name=REGION_NAME,
                    aws_access_key_id=AWS_ACCESS_KEY_ID, 
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                    aws_session_token=AWS_SESSION_TOKEN)
    receipt_handle = message['ReceiptHandle']
    sqs.delete_message(
        QueueUrl=QUEUE_URL,
        ReceiptHandle=receipt_handle
    )



## Run App
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)