from flask import request, jsonify, Blueprint

from app.app import db
from app.auth.models import User

auth = Blueprint("auth", __name__)


@auth.route("/login", methods=["POST"])
def login():
    return


@auth.route("/register", methods=["POST"])
def register():
    return


@auth.route("/me", methods=["GET"])
def me():
    return
