from flask import Flask, request, jsonify
import json
import torch
from model import NeuralNet
from chat import chatbot
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
from dataclasses import asdict
from datetime import datetime


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
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
@cross_origin()
def hello():
    return 'Hello World'

@app.route('/chat/start', methods=['POST'])
@cross_origin()
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

@app.route('/chat/answer', methods=['POST'])
@cross_origin()
def predict():
    if request.method == 'POST':
        conversation_id = request.json['conversation_id']
        question = request.json['question']
        print(question, conversation_id)
        response = chatbot(question, data, model, intents, context=context)
        conversation = Conversation.query.get(conversation_id)
        query = Query(question=question, response=response, conversation_id=conversation.id)
        db.session.add(query)
        db.session.commit()
        print('RESPONSE ', response)
        return jsonify({ 'query': query })
    return jsonify({'error':'Invalid request type'}), 400



@app.route('/chat/resolve', methods=['PUT'])
@cross_origin()
def resolve():
    if request.method == 'PUT':
        try:
            query_id = request.json['query_id']
            conversation_id = request.json['conversation_id']
            print(query_id, conversation_id)
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

@app.route('/chat/contact', methods=['PUT'])
@cross_origin()
def contact():
    if request.method == 'PUT':
        try:
            conversation_id = request.json['conversation_id']
            conversation = Conversation.query.get(conversation_id)
            conversation.contact = True

            db.session.commit()

            return jsonify({'conversation': conversation})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in starting conversation'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@app.route('/conversations', methods=['GET'])
@cross_origin()
def getAllConversations():
    if request.method == 'GET':
        try:
            conversations = Conversation.query.all()
            response = []
            for convo in conversations:
                convoDict = asdict(convo)
                unresolved_queries = Query.query.filter_by(conversation_id=convoDict['id'] , resolved=False).all()
                convoDict['unresolved'] = len(unresolved_queries)
                response.append(convoDict)
        
            return jsonify({'conversations': response})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching all conversations'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/conversations/date', methods=['GET'])
@cross_origin()
def getConversationsByDate():
    if request.method == 'GET':
        year = request.args.get('year')
        month = request.args.get('month')
        day = request.args.get('day')
        startDate  = datetime(year=int(year), month = int(month), day=int(day))
        try:
            conversations = Conversation.query.filter(Conversation.date >= startDate )
            response = []
            for convo in conversations:
                convoDict = asdict(convo)
                unresolved_queries = Query.query.filter_by(conversation_id=convoDict['id'] , resolved=False).all()
                convoDict['unresolved'] = len(unresolved_queries)
                response.append(convoDict)
        
            return jsonify({'conversations': response})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching all conversations'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@app.route('/conversations/daterange', methods=['GET'])
@cross_origin()
def getConversationsByDateRange():
    if request.method == 'GET':
        startYear = request.args.get('startYear')
        startMonth = request.args.get('startMonth')
        startDay = request.args.get('startDay')
        endYear = request.args.get('endYear')
        endMonth = request.args.get('endMonth')
        endDay = request.args.get('endDay')
        startDate  = datetime(year=int(startYear), month = int(startMonth), day=int(startDay))
        endDate = datetime(year=int(endYear), month=int(endMonth), day=int(endDay))
        try:
            conversations = Conversation.query.filter(Conversation.date.between(startDate, endDate)).all()
          
            response = []
            for convo in conversations:
                convoDict = asdict(convo)
                unresolved_queries = Query.query.filter_by(conversation_id=convoDict['id'] , resolved=False).all()
                convoDict['unresolved'] = len(unresolved_queries)
                response.append(convoDict)
        
            return jsonify({'conversations': response})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching all conversations'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/conversations/<conversation_id>', methods=['GET'])
@cross_origin()
def getConversation(conversation_id):
    if request.method  == 'GET':
        try:
            print("CONVO ID: ", conversation_id)
            conversation = Conversation.query.get(conversation_id)
            queries = Query.query.filter_by(conversation_id=conversation_id).all()
            print('CONVO: ', conversation)
            print('Queries: ', queries)
            return jsonify({'conversation': conversation, 'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching conversation'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/queries/', methods=['GET'])
@cross_origin()
def getAllQueries():
    if request.method  == 'GET':
        try:
            queries = Query.query.all()
            print('Queries: ', queries)
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching all queries'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/queries/unresolved', methods=['GET'])
@cross_origin()
def getUnresolvedQueries():
    if request.method  == 'GET':
        try:
            queries = Query.query.filter_by(resolved=False).all()
            print('Unresolved Queries: ', queries)
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching all queries'}), 400

    return jsonify({'error':'Invalid request type'}), 400


    

if __name__ == "__main__":
    app.run()