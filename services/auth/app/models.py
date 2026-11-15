from .extensions import db


class User(db.Model):
    """A system account. Accessed only through the SQLAlchemy ORM."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    forename = db.Column(db.String(256), nullable=False)
    surname = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(32), nullable=False)
