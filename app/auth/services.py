from ..extensions import db, bcrypt
from .models import User, UserRole, Merchant


class AuthError(Exception):
    pass


class ValidationError(AuthError):
    pass


class UserAlreadyExistsError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


def register_user(data):
    if not data:
        raise ValidationError("Request body cannot be empty")

    required_fields = ["email", "password", "name", "surname"]
    missing_fields = [f for f in required_fields if not data.get(f)]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    if User.query.filter_by(email=data.get("email")).first():
        raise UserAlreadyExistsError("User already exists")

    role_string = data.get("role", "user")
    user_role = (
        UserRole.MERCHANT if role_string.lower() == "merchant" else UserRole.USER
    )

    if user_role == UserRole.MERCHANT and not data.get("company_name"):
        raise ValidationError("Merchant must provide a company name")

    hashed_password = bcrypt.generate_password_hash(data.get("password")).decode(
        "utf-8"
    )
    new_user = User(
        email=data.get("email"),
        password_hash=hashed_password,
        name=data.get("name"),
        surname=data.get("surname"),
        role=user_role,
    )
    db.session.add(new_user)

    if user_role == UserRole.MERCHANT:
        new_merchant = Merchant(company_name=data.get("company_name"), user=new_user)
        db.session.add(new_merchant)

    db.session.commit()
    return new_user


def login_user_service(data):
    if not data:
        raise ValidationError("Request body cannot be empty")

    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise ValidationError("Email and password required")

    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password_hash, password):
        return user
    else:
        raise InvalidCredentialsError("Invalid email or password")
