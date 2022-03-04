from flask import Flask, request, jsonify
import json
import torch
from model import NeuralNet
from chat import chatbot
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os


app = Flask(__name__)
CORS(app)

PRODUCTION = False



if PRODUCTION:
    #database string needs to start with postgresql:// not postgres:// which is what heroku sets it to by default and is unchangeable
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)
    app.debug = False
else:
    load_dotenv() #load environment variables for local environment
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:SpicyP#13@localhost/ask-fyeo-chatbot'
    app.debug = True

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('MY_SECRET_KEY')



db = SQLAlchemy(app)

from models import Conversation, Query, Staff
#Model SETUP
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


with open('intents.json', 'r', encoding="utf8") as f:
    intents = json.load(f)


FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()
context = {}





@app.route('/')
def hello():
    return 'Hello World'

@app.route('/chat/start', methods=['POST'])
def start():
    if request.method == 'POST':
        try:
            firstname = request.json['firstname']
            lastname = request.json['lastname']
            program = request.json['program']
            email = request.json['email']

            convo = Conversation(firstname=firstname, lastname=lastname, program=program, email=email)
            db.session.add(convo)
            db.session.commit() 
            return jsonify({'conversation': convo})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in starting conversation'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/chat/<conversation_id>/answer', methods=['POST'])
def predict(conversation_id):
    if request.method == 'POST':
        question = request.json['question']
        print(question)
        response = chatbot(question, data, model, intents, context=context)
        conversation = Conversation.query.get(conversation_id)
        query = Query(question=question, response=response, conversation_id=conversation.id)
        db.session.add(query)
        db.session.commit()
        print('RESPONSE ', response)
        return jsonify({ 'query': query })
    return jsonify({'error':'Invalid request type'}), 400



@app.route('/chat/<conversation_id>/resolve/<query_id>', methods=['PUT'])
def resolve(conversation_id, query_id):
    if request.method == 'PUT':
        try:
            conversation = Conversation.query.get(conversation_id)
            query = Query.query.get(query_id)
            if query.conversation_id != conversation.id:
                return jsonify({'error':'Wrong conversation details'}), 400

            query.resolved = True
            db.session.commit()

            return jsonify({'query': query })
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in starting conversation'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/chat/<conversation_id>/contact', methods=['PUT'])
def contact(conversation_id):
    if request.method == 'PUT':
        try:

            conversation = Conversation.query.get(conversation_id)
            conversation.contact = True

            db.session.commit()

            return jsonify({'conversation': conversation})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in starting conversation'}), 400

    return jsonify({'error':'Invalid request type'}), 400

if __name__ == "__main__":
    app.run()