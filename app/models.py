"""Modelos da V0.0. As relações removem os registros dependentes da garagem."""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from .extensions import db


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(500), default="", nullable=False)
    city = db.Column(db.String(80), default="", nullable=False)
    photo = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    vehicles = db.relationship(
        "Vehicle",
        back_populates="owner",
        cascade="all, delete-orphan",
        order_by="Vehicle.id.desc()",
    )
    posts = db.relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(80), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(40), nullable=False)
    engine = db.Column(db.String(80), default="", nullable=False)
    transmission = db.Column(db.String(50), default="", nullable=False)
    description = db.Column(db.String(2000), default="", nullable=False)
    viewer_config = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    owner = db.relationship("User", back_populates="vehicles")
    photos = db.relationship(
        "VehiclePhoto",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        order_by="VehiclePhoto.id",
    )
    stats = db.relationship(
        "CarStats",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        order_by="(CarStats.date, CarStats.id)",
    )
    modifications = db.relationship(
        "Modification",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        order_by="Modification.date.desc()",
    )

    @property
    def title(self):
        return f"{self.brand} {self.model}"

    @property
    def latest_stats(self):
        return self.stats[-1] if self.stats else None


class VehiclePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    vehicle = db.relationship("Vehicle", back_populates="photos")


class CarStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    power = db.Column(db.Float, nullable=False)
    torque = db.Column(db.Float)
    zero_to_hundred = db.Column(db.Float)
    top_speed = db.Column(db.Float)
    consumption = db.Column(db.Float)
    vehicle = db.relationship("Vehicle", back_populates="stats")


class Modification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicle.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Numeric(12, 2), nullable=False)
    vehicle = db.relationship("Vehicle", back_populates="modifications")


class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    __table_args__ = (db.CheckConstraint("follower_id != followed_id"),)


class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_low_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user_high_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(10), default="pending", nullable=False)
    __table_args__ = (
        db.UniqueConstraint("user_low_id", "user_high_id"),
        db.CheckConstraint("user_low_id < user_high_id"),
        db.CheckConstraint("status IN ('pending', 'accepted')"),
    )

    def other_id(self, user_id):
        return self.user_high_id if user_id == self.user_low_id else self.user_low_id


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )
    text = db.Column(db.String(2000), default="", nullable=False)
    photo = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now, nullable=False, index=True)
    author = db.relationship("User", back_populates="posts")
    likes = db.relationship("Like", cascade="all, delete-orphan", back_populates="post")
    comments = db.relationship(
        "Comment",
        cascade="all, delete-orphan",
        back_populates="post",
        order_by="Comment.created_at",
    )


class Like(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), primary_key=True)
    post = db.relationship("Post", back_populates="likes")


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)
    text = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=now, nullable=False)
    author = db.relationship("User")
    post = db.relationship("Post", back_populates="comments")
