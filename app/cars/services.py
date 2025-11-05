from ..extensions import db
from .models import Car
from app.auth.models import Merchant


class CarError(Exception):
    pass


class CarNotFoundError(CarError):
    pass


class ValidationError(CarError):
    pass


def create_car(data, merchant_id):
    if not data:
        raise ValidationError("Request body cannot be empty")

    required_fields = ["make", "model", "year", "price_per_hour"]
    missing_fields = []

    for field in required_fields:
        if not data.get(field):
            missing_fields.append(field)

    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    new_car = Car(
        make=data.get("make"),
        model=data.get("model"),
        year=data.get("year"),
        price_per_hour=data.get("price_per_hour"),
        merchant_id=merchant_id,
    )

    db.session.add(new_car)
    db.session.commit()
    return new_car


def get_merchant_cars(merchant_id):
    return Car.query.filter_by(merchant_id=merchant_id).all()
