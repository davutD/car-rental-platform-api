from decimal import Decimal, InvalidOperation
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
    cars = Car.query.filter_by(merchant_id=int(merchant_id)).all()
    if not cars:
        raise CarNotFoundError("Merchant has no cars to list")
    return cars


def update_car(car_id, data, merchant_id):
    if not data:
        raise ValidationError("Request body cannot be empty")

    car = Car.query.filter_by(id=int(car_id), merchant_id=int(merchant_id)).first()
    if not car:
        raise CarNotFoundError("Car not found")

    try:
        if "make" in data:
            car.make = data["make"]
        if "model" in data:
            car.model = data["model"]
        if "year" in data:
            car.year = int(data["year"])
        if "price_per_hour" in data:
            car.price_per_hour = Decimal(data["price_per_hour"])
        if "status" in data:
            car.status = data["status"]

        db.session.commit()
        return car

    except (ValueError, TypeError, InvalidOperation) as e:
        db.session.rollback()
        raise ValidationError(f"Invalid data format: {e}")
    except Exception as e:
        db.session.rollback()
        raise Exception(str(e))


def delete_car(car_id, merchant_id):
    car = Car.query.filter_by(id=int(car_id), merchant_id=int(merchant_id)).first()
    if not car:
        raise CarNotFoundError("Car not found")
    db.session.delete(car)
    db.session.commit()
    return {"message": "Successfully deleted"}


def get_car(car_id):
    car = Car.query.get(int(car_id))
    if not car:
        raise CarNotFoundError("No car to display for this id")
    return car
