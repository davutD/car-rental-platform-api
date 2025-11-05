from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user, current_user, login_required

from ..extensions import db, login_manager, bcrypt
from app.auth.models import User, Merchant, UserRole

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
        if not data:
            return jsonify({"error": "Request body cannot be empty"}), 400

        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"error": "Invalid email or password"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@auth.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body cannot be empty"}), 400

        required_fields = ["email", "password", "name", "surname"]
        missing_fields = []

        for field in required_fields:
            if not data.get(field):
                missing_fields.append(field)

        if missing_fields:
            return (
                jsonify(
                    {"error": f"Missing required fields: {', '.join(missing_fields)}"}
                ),
                400,
            )

        if User.query.filter_by(email=data.get("email")).first():
            return jsonify({"error": "User already exists"}), 409

        hashed_password = bcrypt.generate_password_hash(data.get("password")).decode(
            "utf-8"
        )
        role_string = data.get("role", "user")
        user_role = (
            UserRole.MERCHANT if role_string.lower() == "merchant" else UserRole.USER
        )

        if user_role == UserRole.MERCHANT and not data.get("company_name"):
            return jsonify({"error": "Merchant must provide a company name"}), 400

        new_user = User(
            email=data.get("email"),
            password_hash=hashed_password,
            name=data.get("name"),
            surname=data.get("surname"),
            role=user_role,
        )
        db.session.add(new_user)

        if user_role == UserRole.MERCHANT:
            new_merchant = Merchant(
                company_name=data.get("company_name"), user=new_user
            )
            db.session.add(new_merchant)

        db.session.commit()
        return jsonify({"message": "User registered successfully"}), 201
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
