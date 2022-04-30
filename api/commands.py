import click
from flask.cli import with_appcontext
from flask import  current_app
import json

from .database import db, FAQ


@click.command(name='faq_init')
@with_appcontext
def faq_init():
    with open('intents.json', 'r', encoding='utf8') as f:
        file_data = json.loads(f.read())
        for q in file_data['intents']:
            print(q)
            tag = q['tag']
            patterns = q['patterns']
            responses = q['responses']

            if len(list(filter(lambda p: p.find('|') != -1, patterns))) > 0 or len(list(filter(lambda r: r.find('|') != -1, responses))) > 0:
                continue

            patterns = '|'.join(patterns)
            responses = '|'.join(responses)

            new_faq = FAQ(tag=tag, patterns=patterns, responses=responses)
            db.session.add(new_faq)
        
        db.session.commit()

@click.command(name='train_model')
@with_appcontext
def train_model():
    current_app.config['chatbot'].train()


@click.command(name='chat')
@with_appcontext
def chat():
    current_app.config['chatbot'].chat()



@click.command(name='view_intents')
@with_appcontext
def view_intents():
    with open('intents.json', 'r', encoding='utf8') as f:
        file_data = json.loads(f.read())
        for q in file_data['intents']:
            print(q)
            
