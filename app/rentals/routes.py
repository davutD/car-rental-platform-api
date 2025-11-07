from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.utils.decorators import role_required
from app.auth.models import UserRole
from . import services
from .services import (
    UserAlreadyRentingError,
    CarNotAvailableError,
    CarNotFoundError,
    NoActiveRentalError,
)

rentals = Blueprint("rentals", __name__)


@rentals.route("/rent/<int:car_id>", methods=["POST"])
@login_required
@role_required(UserRole.USER)
def rent_a_car(car_id):
    try:
        user_id = current_user.id
        new_rental = services.rent_a_car(user_id, car_id)
        return jsonify(new_rental.to_dict()), 201
    except (UserAlreadyRentingError, CarNotAvailableError) as e:
        return jsonify({"error": str(e)}), 409
    except CarNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rentals.route("/return", methods=["POST"])
@login_required
@role_required(UserRole.USER)
def return_car():
    try:
        user_id = current_user.id
        completed_rental = services.return_car(user_id)
        return jsonify(completed_rental.to_dict()), 200
    except NoActiveRentalError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rentals.route("/history", methods=["GET"])
@login_required
@role_required(UserRole.USER)
def get_rental_history():
    try:
        user_id = current_user.id
        rentals = services.get_rental_history(user_id)
        return jsonify([rental.to_dict() for rental in rentals]), 200
    except NoActiveRentalError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
