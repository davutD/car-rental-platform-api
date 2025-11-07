from decimal import Decimal, InvalidOperation
from datetime import datetime
from sqlalchemy import func, cast, Date
from ..extensions import db
from .models import Rental
from app.cars.models import Car, CarStatus


class RentalError(Exception):
    pass


class UserAlreadyRentingError(RentalError):
    pass


class CarNotAvailableError(RentalError):
    pass


class CarNotFoundError(RentalError):
    pass


class NoActiveRentalError(RentalError):
    pass


class ValidationError(RentalError):
    pass


def rent_a_car(user_id, car_id):
    active_rental = Rental.query.filter_by(user_id=user_id, return_date=None).first()
    if active_rental:
        raise UserAlreadyRentingError("User already has an active rental")
    car = Car.query.get(car_id)
    if not car:
        raise CarNotFoundError("Car not found")

    if car.status != CarStatus.AVAILABLE:
        raise CarNotAvailableError("This car is not available for rent")

    try:
        car.status = CarStatus.RENTED
        new_rental = Rental(user_id=user_id, car_id=car_id)
        db.session.add(new_rental)
        db.session.add(car)
        db.session.commit()

        return new_rental

    except Exception as e:
        db.session.rollback()
        raise Exception(str(e))


def return_car(user_id):
    active_rental = Rental.query.filter_by(user_id=user_id, return_date=None).first()
    if not active_rental:
        raise NoActiveRentalError("User do not have an active rental to return")

    car = active_rental.car
    return_time = datetime.utcnow()
    rental_duration = return_time - active_rental.rental_date
    total_hours = rental_duration.total_seconds() / 3600.0
    total_fee = car.price_per_hour * Decimal(total_hours)

    try:
        active_rental.return_date = return_time
        active_rental.total_fee = total_fee
        car.status = CarStatus.AVAILABLE
        db.session.add(active_rental)
        db.session.add(car)
        db.session.commit()

        return active_rental

    except Exception as e:
        db.session.rollback()
        raise Exception(f"Database error on return: {e}")


def get_rental_history(user_id):
    rentals = (
        Rental.query.filter_by(user_id=user_id)
        .order_by(Rental.rental_date.desc())
        .all()
    )

    if not rentals:
        raise NoActiveRentalError("You have no rental history")

    return rentals


def query_user_rentals(user_id, query_params):
    query = Rental.query.filter_by(user_id=user_id)

    try:
        page_number = int(query_params.get("page", 1))
        per_page = int(query_params.get("per_page", 10))
    except ValueError:
        raise ValidationError("Invalid page or per_page parameter. Must be an integer")
    if page_number < 1:
        raise ValidationError("Page number must be 1 or greater")
    if per_page < 1:
        raise ValidationError("Per_page must be 1 or greater")

    car_filters = {"make", "model", "year", "min_price_per_hour", "max_price_per_hour"}
    if any(k in query_params and query_params.get(k) for k in car_filters):
        query = query.join(Car)

    try:
        if "car_id" in query_params and query_params.get("car_id"):
            query = query.filter(Rental.car_id == int(query_params.get("car_id")))

        if "min_fee" in query_params and query_params.get("min_fee"):
            query = query.filter(
                Rental.total_fee >= Decimal(query_params.get("min_fee"))
            )
        if "max_fee" in query_params and query_params.get("max_fee"):
            query = query.filter(
                Rental.total_fee <= Decimal(query_params.get("max_fee"))
            )

        if "status" in query_params and query_params.get("status"):
            status = query_params.get("status").lower()
            if status == "active":
                query = query.filter(Rental.return_date == None)
            elif status == "completed":
                query = query.filter(Rental.return_date != None)
            else:
                raise ValidationError("Invalid status. Must be 'active' or 'completed'")

        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError(
                    f"Invalid date format: '{date_str}'. Must be YYYY-MM-DD"
                )

        if "rental_date_start" in query_params and query_params.get(
            "rental_date_start"
        ):
            start_date = parse_date(query_params.get("rental_date_start"))
            query = query.filter(cast(Rental.rental_date, Date) >= start_date)

        if "rental_date_end" in query_params and query_params.get("rental_date_end"):
            end_date = parse_date(query_params.get("rental_date_end"))
            query = query.filter(cast(Rental.rental_date, Date) <= end_date)

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

        if "max_price_per_hour" in query_params and query_params.get(
            "max_price_per_hour"
        ):
            max_price = Decimal(query_params.get("max_price_per_hour"))
            query = query.filter(Car.price_per_hour <= max_price)

        if "min_price_per_hour" in query_params and query_params.get(
            "min_price_per_hour"
        ):
            min_price = Decimal(query_params.get("min_price_per_hour"))
            query = query.filter(Car.price_per_hour >= min_price)

    except (ValueError, TypeError, InvalidOperation) as e:
        db.session.rollback()
        raise ValidationError(f"Invalid filter data type: {e}")

    paginated_rentals = query.order_by(Rental.rental_date.desc()).paginate(
        page=page_number, per_page=per_page, error_out=False
    )

    if not paginated_rentals.items and page_number == 1:
        raise CarNotFoundError("No rentals found matching your criteria")

    return paginated_rentals


def get_merchant_rental_history(merchant_id):
    rentals = (
        db.session.query(Rental)
        .join(Car)
        .filter(Car.merchant_id == merchant_id)
        .order_by(Rental.rental_date.desc())
        .all()
    )

    if not rentals:
        raise CarNotFoundError("No rental history found for your cars")

    return rentals


def query_merchant_rentals(merchant_id, query_params):
    query = db.session.query(Rental).join(Car).filter(Car.merchant_id == merchant_id)

    try:
        page_number = int(query_params.get("page", 1))
        per_page = int(query_params.get("per_page", 10))
    except ValueError:
        raise ValidationError("Invalid page or per_page parameter. Must be an integer")
    if page_number < 1:
        raise ValidationError("Page number must be 1 or greater")
    if per_page < 1:
        raise ValidationError("Per_page must be 1 or greater")

    try:
        if "car_id" in query_params and query_params.get("car_id"):
            query = query.filter(Rental.car_id == int(query_params.get("car_id")))

        if "user_id" in query_params and query_params.get("user_id"):
            query = query.filter(Rental.user_id == int(query_params.get("user_id")))

        if "min_fee" in query_params and query_params.get("min_fee"):
            query = query.filter(
                Rental.total_fee >= Decimal(query_params.get("min_fee"))
            )
        if "max_fee" in query_params and query_params.get("max_fee"):
            query = query.filter(
                Rental.total_fee <= Decimal(query_params.get("max_fee"))
            )

        if "status" in query_params and query_params.get("status"):
            status = query_params.get("status").lower()
            if status == "active":
                query = query.filter(Rental.return_date == None)
            elif status == "completed":
                query = query.filter(Rental.return_date != None)
            else:
                raise ValidationError("Invalid status. Must be 'active' or 'completed'")

        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError(
                    f"Invalid date format: '{date_str}'. Must be YYYY-MM-DD"
                )

        if "rental_date_start" in query_params and query_params.get(
            "rental_date_start"
        ):
            start_date = parse_date(query_params.get("rental_date_start"))
            query = query.filter(cast(Rental.rental_date, Date) >= start_date)

        if "rental_date_end" in query_params and query_params.get("rental_date_end"):
            end_date = parse_date(query_params.get("rental_date_end"))
            query = query.filter(cast(Rental.rental_date, Date) <= end_date)

    except (ValueError, TypeError, InvalidOperation) as e:
        db.session.rollback()
        raise ValidationError(f"Invalid filter data type: {e}")

    paginated_rentals = query.order_by(Rental.rental_date.desc()).paginate(
        page=page_number, per_page=per_page, error_out=False
    )

    if not paginated_rentals.items and page_number == 1:
        raise CarNotFoundError("No rentals found for your cars")

    return paginated_rentals
