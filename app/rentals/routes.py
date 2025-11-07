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
    ValidationError,
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


@rentals.route("/user/history", methods=["GET"])
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


@rentals.route("/user/query", methods=["GET"])
@login_required
@role_required(UserRole.USER)
def query_user_rentals():
    try:
        user_id = current_user.id
        query_params = request.args.to_dict()
        pagination_obj = services.query_user_rentals(user_id, query_params)
        rentals_list = [rental.to_dict() for rental in pagination_obj.items]
        pagination_meta = {
            "page": pagination_obj.page,
            "per_page": pagination_obj.per_page,
            "total_pages": pagination_obj.pages,
            "total_items": pagination_obj.total,
        }

        return jsonify({"rentals": rentals_list, "pagination": pagination_meta}), 200

    except (CarNotFoundError, NoActiveRentalError) as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rentals.route("/merchant/history", methods=["GET"])
@login_required
@role_required(UserRole.MERCHANT)
def get_merchant_rental_history():
    try:
        merchant_id = current_user.merchant_profile.id
        rentals = services.get_merchant_rental_history(merchant_id)
        return jsonify([rental.to_dict() for rental in rentals]), 200

    except CarNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@rentals.route("/merchant/query", methods=["GET"])
@login_required
@role_required(UserRole.MERCHANT)
def query_merchant_rentals():
    try:
        merchant_id = current_user.merchant_profile.id
        query_params = request.args.to_dict()

        pagination_obj = services.query_merchant_rentals(merchant_id, query_params)

        rentals_list = [rental.to_dict() for rental in pagination_obj.items]
        pagination_meta = {
            "page": pagination_obj.page,
            "per_page": pagination_obj.per_page,
            "total_pages": pagination_obj.pages,
            "total_items": pagination_obj.total,
        }

        return jsonify({"rentals": rentals_list, "pagination": pagination_meta}), 200

    except (CarNotFoundError, NoActiveRentalError) as e:
        return jsonify({"error": str(e)}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
