from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required

from ..extensions import db, login_manager
from app.auth.models import User

from . import services
from .services import ValidationError, UserAlreadyExistsError, InvalidCredentialsError

auth = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@auth.route("/login", methods=["POST"])
def login():
    try:
        if current_user.is_authenticated:
            return jsonify({"error": "User is already logged in"}), 200

        data = request.get_json()
        user_to_login = services.login_user_service(data)
        login_user(user_to_login)
        return jsonify({"message": "Login successful"}), 200

    except (ValidationError, InvalidCredentialsError) as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        services.register_user(data)
        return jsonify({"message": "User registered successfully"}), 201

    except ValidationError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except UserAlreadyExistsError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    try:
        logout_user()
        return jsonify({"message": "Successfully logged out!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth.route("/me", methods=["GET"])
@login_required
def me():
    try:
        user_data = {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "surname": current_user.surname,
            "role": current_user.role.value,
        }
        return jsonify(user_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
