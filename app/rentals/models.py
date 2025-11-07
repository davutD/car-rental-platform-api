from datetime import datetime
from ..extensions import db


class Rental(db.Model):
    __tablename__ = "rentals"

    id = db.Column(db.Integer, primary_key=True)
    rental_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    total_fee = db.Column(db.Numeric(10, 2), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id"), nullable=False)
    user = db.relationship("User", back_populates="rentals")
    car = db.relationship("Car", back_populates="rentals")

    def __repr__(self):
        return f"<Rental {self.id} - User {self.user_id} rented Car {self.car_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "car_id": self.car_id,
            "rental_date": self.rental_date.isoformat(),
            "return_date": self.return_date.isoformat() if self.return_date else None,
            "total_fee": str(self.total_fee) if self.total_fee else None,
        }
