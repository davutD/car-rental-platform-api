import enum
from app.app import db
from flask_login import UserMixin


class UserRole(enum.Enum):
    USER = "user"
    MERCHANT = "merchant"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    surname = db.Column(db.String(80), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER)
    merchant_profile = db.relationship(
        "Merchant", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    # rentals = db.relationship(
    #     "Rental", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    # )

    def __repr__(self):
        return f"<User {self.email}, {self.name} {self.surname}>"

    def get_id(self):
        return self.id


class Merchant(db.Model):
    __tablename__ = "merchants"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(120), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )
    user = db.relationship("User", back_populates="merchant_profile")
    # cars = db.relationship(
    #     "Car", back_populates="merchant", lazy="dynamic", cascade="all, delete-orphan"
    # )

    def __repr__(self):
        return f"<Merchant {self.company_name} >"
