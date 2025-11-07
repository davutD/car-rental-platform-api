from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.utils.decorators import role_required
from app.auth.models import UserRole
from . import services
from .services import CarNotFoundError, ValidationError


cars = Blueprint("cars", __name__)


@cars.route("/create", methods=["POST"])
@login_required
@role_required(UserRole.MERCHANT)
def create_car():
    try:
        data = request.get_json()
        merchant_id = current_user.merchant_profile.id
        new_car = services.create_car(data, merchant_id)
        return jsonify(new_car.to_dict()), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cars.route("/my-cars", methods=["GET"])
@login_required
@role_required(UserRole.MERCHANT)
def get_merchant_cars():
    try:
        merchant_id = current_user.merchant_profile.id
        cars = services.get_merchant_cars(merchant_id)
        return jsonify([car.to_dict() for car in cars]), 200
    except CarNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cars.route("/<int:car_id>", methods=["PUT"])
@login_required
@role_required(UserRole.MERCHANT)
def update_merchant_car(car_id):
    try:
        data = request.get_json()
        merchant_id = current_user.merchant_profile.id
        updated_car = services.update_car(car_id, data, merchant_id)
        return jsonify(updated_car.to_dict()), 200
    except CarNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cars.route("/<int:car_id>", methods=["DELETE"])
@login_required
@role_required(UserRole.MERCHANT)
def delete_merchant_car(car_id):
    try:
        merchant_id = current_user.merchant_profile.id
        result = services.delete_car(car_id, merchant_id)
        return jsonify(result)
    except CarNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@cars.route("/<int:car_id>", methods=["GET"])
def get_merchant_car(car_id):
    try:
        car = services.get_car(car_id)
        return jsonify(car.to_dict()), 200
    except CarNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
