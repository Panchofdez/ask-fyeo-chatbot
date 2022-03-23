from app import db
from datetime import datetime
from dataclasses import dataclass



@dataclass
class Conversation(db.Model):
    __tablename__ = 'conversation'
    id:int
    firstname: str
    lastname: str
    program:str
    email: str
    contact:bool
    date: datetime


    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(200), nullable=False)
    lastname = db.Column(db.String(200), nullable=False)
    program = db.Column(db.String(200))
    email = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.Boolean, nullable=False,  default=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    queries = db.relationship('Query', backref='author', lazy=True)



@dataclass
class Query(db.Model):
    __tablename__ = 'query'
    id:int
    question: str
    response: str
    resolved: bool
    conversation_id: int


    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    response = db.Column(db.String, nullable=False)
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)



@dataclass
class Staff(db.Model):
    id:int
    email:str

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    

