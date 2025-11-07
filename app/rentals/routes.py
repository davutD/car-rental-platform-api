from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user


rentals = Blueprint("rentals", __name__)


@rentals.route("/")
def index():
    return jsonify({"message": "Welcome to the Car Rental API!"}), 200
