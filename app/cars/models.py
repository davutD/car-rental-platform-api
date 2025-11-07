import enum
from ..extensions import db


class CarStatus(enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"


class Car(db.Model):
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(CarStatus), nullable=False, default=CarStatus.AVAILABLE)
    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)

    merchant_id = db.Column(db.Integer, db.ForeignKey("merchants.id"), nullable=False)
    merchant = db.relationship("Merchant", back_populates="cars")
    rentals = db.relationship("Rental", back_populates="car", lazy="dynamic")

    def __repr__(self):
        return f"<Car {self.year} {self.make} {self.model}>"

    def to_dict(self):
        return {
            "id": self.id,
            "make": self.make,
            "model": self.model,
            "year": self.year,
            "status": self.status.value,
            "price_per_hour": str(self.price_per_hour),
            "merchant_id": self.merchant_id,
        }
