from flask import Blueprint, jsonify

core = Blueprint("core", __name__)


@core.route("/")
def index():
    return jsonify({"message": "Welcome to the Car Rental API!"}), 200
