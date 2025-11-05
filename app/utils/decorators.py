from functools import wraps
from flask import jsonify
from flask_login import current_user
from app.auth.models import UserRole


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Authentication required"}), 401

            if current_user.role != role:
                return (
                    jsonify(
                        {"error": f"Access forbidden: Requires '{role.value}' role"}
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated_function

    return decorator
