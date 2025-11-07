from decimal import Decimal, InvalidOperation
from ..extensions import db
from .models import Car, CarStatus
from app.auth.models import Merchant
from sqlalchemy import func


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


def get_all_cars():
    cars = Car.query.all()
    if not cars:
        raise CarNotFoundError("No car to display")
    return cars


def query_cars(query_params):
    query = Car.query.filter_by(status=CarStatus.AVAILABLE)

    try:
        page_number = int(query_params.get("page", 1))
        per_page = int(query_params.get("per_page", 10))
    except ValueError:
        raise ValidationError("Invalid page or per_page parameter. Must be an integer")
    if page_number < 1:
        raise ValidationError("Page number must be 1 or greater.")
    if per_page < 1:
        raise ValidationError("Per_page must be 1 or greater.")

    try:
        if "make" in query_params and query_params.get("make"):
            query = query.filter(
                func.lower(Car.make) == query_params.get("make").lower()
            )
        if "model" in query_params and query_params.get("model"):
            query = query.filter(
                func.lower(Car.model) == query_params.get("model").lower()
            )
        if "year" in query_params and query_params.get("year"):
            query = query.filter(Car.year == int(query_params.get("year")))
        if "max_price" in query_params and query_params.get("max_price"):
            max_price = Decimal(query_params.get("max_price"))
            query = query.filter(Car.price_per_hour <= max_price)
        if "min_price" in query_params and query_params.get("min_price"):
            min_price = Decimal(query_params.get("min_price"))
            query = query.filter(Car.price_per_hour >= min_price)
        if "merchant_id" in query_params and query_params.get("merchant_id"):
            query = query.filter(
                Car.merchant_id == int(query_params.get("merchant_id"))
            )
    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValidationError(f"Invalid filter data type {e}")

    paginated_cars = query.paginate(
        page=page_number, per_page=per_page, error_out=False
    )

    if not paginated_cars.items and page_number == 1:
        raise CarNotFoundError("No cars found matching your criteria")

    return paginated_cars


def query_merchant_cars(merchant_id, query_params):
    query = Car.query.filter_by(merchant_id=merchant_id)

    try:
        page_number = int(query_params.get("page", 1))
        per_page = int(query_params.get("per_page", 10))
    except ValueError:
        raise ValidationError("Invalid page or per_page parameter. Must be an integer.")

    if page_number < 1:
        raise ValidationError("Page number must be 1 or greater.")
    if per_page < 1:
        raise ValidationError("Per_page must be 1 or greater.")

    try:
        if "status" in query_params and query_params.get("status"):
            car_status = query_params.get("status").lower()
            if car_status == "available":
                query = query.filter(Car.status == CarStatus.AVAILABLE)
            elif car_status == "rented":
                query = query.filter(Car.status == CarStatus.RENTED)
            else:
                raise ValidationError(
                    f"Invalid status value '{query_params.get('status')}'. "
                    "Must be 'available' or 'rented'."
                )

        if "make" in query_params and query_params.get("make"):
            query = query.filter(
                func.lower(Car.make) == query_params.get("make").lower()
            )
        if "model" in query_params and query_params.get("model"):
            query = query.filter(
                func.lower(Car.model) == query_params.get("model").lower()
            )
        if "year" in query_params and query_params.get("year"):
            query = query.filter(Car.year == int(query_params.get("year")))
        if "max_price" in query_params and query_params.get("max_price"):
            max_price = Decimal(query_params.get("max_price"))
            query = query.filter(Car.price_per_hour <= max_price)
        if "min_price" in query_params and query_params.get("min_price"):
            min_price = Decimal(query_params.get("min_price"))
            query = query.filter(Car.price_per_hour >= min_price)

    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValidationError(f"Invalid filter data type: {e}")

    paginated_cars = query.paginate(
        page=page_number, per_page=per_page, error_out=False
    )

    if not paginated_cars.items and page_number == 1:
        raise CarNotFoundError("No cars found in your listings")

    return paginated_cars
