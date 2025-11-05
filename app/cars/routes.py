from flask import Blueprint, jsonify, request

from ..extensions import db
from app.cars.models import Car


cars = Blueprint("cars", __name__)
