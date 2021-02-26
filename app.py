from flask import Flask, jsonify, request, g
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from sqlalchemy import Column, String
import os
from middleware import use_middleware
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config["JWT_SECRET_KEY"] = "super-secret"
app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
# app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
# app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']

jwt = JWTManager(app)

db = SQLAlchemy(app)
ma = Marshmallow(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    db.create_all()
    print('db created')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('db deleted')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='mercury',
                     planet_type='class D')
    not_mercury = Planet(planet_name='mercury',
                         planet_type='class D')

    db.session.add(mercury)
    db.session.add(not_mercury)

    test_user = User(name='vika',
                     last_name='po',
                     email='vika@',
                     password='1234')

    db.session.add(test_user)
    db.session.commit()
    print('seeded')


@app.route('/url/<string:name>')
def hello_world(name: str):
    return jsonify(message=name)


@app.route('/')
@use_middleware
def hello_world2():

    return f'token {g.token}'


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/register', methods=["POST"])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='user exist'), 404
    else:
        name = request.form['name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        user = User(name=name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='user created'), 201


@app.route('/login', methods=["POST"])
def login():
    if request.is_json:
        email = request.json["email"]
        password = request.json["password"]
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='you are loged in', access_token=access_token)
    else:
        return jsonify(message='bad email'), 401


@app.route('/retrieve/<int:planet_id>', methods=['GET'])
def retrieve(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        res = planet_schema.dump(planet)
        return jsonify(res.data)
    return jsonify(message='doesnt exist'), 404


@app.route('/add', methods=['POST'])
@jwt_required()
def add():
    planet = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet).first()
    if test:
        return jsonify(message='planet already exist'), 404
    else:
        planet_type = request.form['planet_type']
        new_planet = Planet(planet_name=planet, planet_type=planet_type)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify(message='planet created'), 201


@app.route('/update', methods=['PUT'])
@jwt_required()
def update():
    planet_id = request.form['planet_id']
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        db.session.commit()
        return jsonify(message='planet updated'), 202
    else:
        return jsonify(message='planet does not exist'), 404


@app.route('/delete<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete(planet_id):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message='planet deleted')


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    last_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = db.Column(db.Integer, primary_key=True)
    planet_name = db.Column(db.String(200), nullable=False)
    planet_type = Column(String(200), nullable=False)


class UserSchema(ma.Schema):
    class Meta:
        __tablename__ = 'users'
        fields = ("id", "name",  "last_name",  "email", "password")


class PlanetSchema(ma.Schema):
    class Meta:
        __tablename__ = 'planets'
        fields = ("planet_id", "planet_name",  "planet_type")


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run()
