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
    faq_id:int

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String, nullable=False)
    response = db.Column(db.String, nullable=False)
    resolved = db.Column(db.Boolean, nullable=False, default=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    faq_id = db.Column(db.Integer, db.ForeignKey('faq.id'), nullable=True)



@dataclass
class Staff(db.Model):
    __tablename__ = 'staff'
    id:int
    email:str

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)



@dataclass
class FAQ(db.Model):
    __tablename__ = 'faq'
    id:int
    tag: str
    patterns: str
    responses: str

    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String, unique=True, nullable=False)
    patterns = db.Column(db.String, nullable=False)
    responses = db.Column(db.String, nullable=False)
    queries = db.relationship('Query', backref='parent', lazy=True)
    

