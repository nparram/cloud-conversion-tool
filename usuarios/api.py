from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////mnt/usuarios.db'
db = SQLAlchemy(app)
ma = Marshmallow(app)
app.config["JWT_SECRET_KEY"] = "cloud-conversor-jwt"

jwt = JWTManager(app)
api = Api(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    email = db.Column(db.String(50), unique=True)

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
                                       User.contrasena == request.json["password"]).first()
        db.session.commit()
        if user is None:
            return "El usuario no existe", 404
        else:
            token = create_access_token(identity=usuario.id)
            return {"mensaje": "Inicio de sesión exitoso", "token": token}

api.add_resource(AuthSignupResource, '/api/auth/signup')
api.add_resource(AuthLoginResource, '/api/auth/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', ssl_context='adhoc')

