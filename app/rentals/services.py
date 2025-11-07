from decimal import Decimal
from datetime import datetime
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
