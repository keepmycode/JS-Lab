from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    username  = db.Column(db.String(80), unique=True, nullable=False)
    password  = db.Column(db.String(200), nullable=False)
    progress  = db.relationship('UserTaskProgress', backref='user', lazy=True)

class UserTaskProgress(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    level     = db.Column(db.Integer, nullable=False)
    task_idx  = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'level', 'task_idx', name='uniq_progress'),
    )
