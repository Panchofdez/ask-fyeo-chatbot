from re import A
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
from datetime import datetime, timedelta
from sqlalchemy.sql.functions import func
import jwt 
from functools import wraps

app = Flask(__name__)
CORS(app)
# app.config['CORS_HEADERS'] = 'Content-Type'
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


def token_required(func):
    '''Decorator that acts as a middleware to check if a user is signed before accessing route'''
    @wraps(func)
    def inner(*args, **kwargs):
        print(request.headers)
        auth_header = request.headers.get('authorization')
        user= None
        print("header", auth_header)
        if auth_header:
            token = auth_header.replace("Bearer ", "")
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'],  algorithms=["HS256"])
                user = Staff.query.filter_by(email=data['email']).first()
            except Exception as e:
                print("ERROR in getting user: ", e)
                return jsonify({'error':'Not Authorized'}), 403
        else:
            return jsonify({'error':'Not Authorized'}), 401
        return func(user, *args, **kwargs)
    return inner



@app.route('/')
@cross_origin()
def hello():
    return 'Hello World'


@app.route('/login', methods=['POST'])
@cross_origin()
def login():
    if request.method == 'POST':
        try:
            email = request.json['email']
            password = request.json['password']
            user = Staff.query.filter_by(email=email).first()

            print(email)
            if user is None:
                return jsonify({'error':'Invalid email'}), 403

            if password != os.environ.get('FYEO_PASSWORD'):
                return jsonify({'error':'Invalid credentials'}), 403
            token = jwt.encode({'email': user.email,'exp' : datetime.utcnow() + timedelta(minutes=45)},  app.config['SECRET_KEY'], algorithm="HS256")

            print(token)

            return jsonify({'token': token})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error logging in'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@app.route('/staff', methods=['GET'])
@cross_origin()
@token_required
def getStaff(user):

    if request.method == 'GET':
        try:
            all_staff = Staff.query.all()

            return jsonify({'staff': all_staff })
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error retrieving all staff members'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/staff', methods=['POST'])
@cross_origin()
@token_required
def addStaff(user):

    if request.method == 'POST':
        try:
            email = request.json['email']
            new_staff = Staff(email=email)
            db.session.add(new_staff)
            db.session.commit()

            all_staff = Staff.query.all()

            return jsonify({'staff': all_staff })
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error adding staff member'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@app.route('/staff', methods=['DELETE'])
@cross_origin()
@token_required
def removeStaff(user):

    if request.method == 'DELETE':
        try:
            email = request.json['email']
            user = Staff.query.filter_by(email=email).first()
            db.session.delete(user)
            db.session.commit()
            all_staff = Staff.query.all()
            return jsonify({'staff': all_staff })
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error removing staff member'}), 400

    return jsonify({'error':'Invalid request type'}), 400


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
@token_required
def getAllConversations(user):
    if request.method == 'GET':
        try:
            conversations = Conversation.query.order_by(Conversation.date.desc()).all()
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
@token_required
def getConversationsByDate(user):
    if request.method == 'GET':
        try:
            year = request.args.get('year')
            month = request.args.get('month')
            day = request.args.get('day')
            print(year, month, day)
            startDate  = datetime(year=int(year), month = int(month), day=int(day)) # datetime day and months starts at 1, javascript months start at 0
            print(startDate)
        
            conversations = Conversation.query.filter(Conversation.date >= startDate ).order_by(Conversation.date.desc())
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
@token_required
def getConversationsByDateRange(user):
    if request.method == 'GET':
        try:
            startYear = request.args.get('startYear')
            startMonth = request.args.get('startMonth')
            startDay = request.args.get('startDay')
            endYear = request.args.get('endYear')
            endMonth = request.args.get('endMonth')
            endDay = request.args.get('endDay')
            startDate  = datetime(year=int(startYear), month = int(startMonth), day=int(startDay))
            endDate = datetime(year=int(endYear), month=int(endMonth), day=int(endDay))
            print(startDate, endDate)
        
            conversations = Conversation.query.filter(Conversation.date.between(startDate, endDate)).order_by(Conversation.date.desc()).all()
          
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
@token_required
def getConversation(user,conversation_id):
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


@app.route('/conversation/<conversation_id>', methods=['PUT'])
@cross_origin()
@token_required
def updateConversation(user,conversation_id):
    if request.method == 'PUT':
        try:
            print("CONVO ID: ", conversation_id)
            conversation = Conversation.query.get(conversation_id)
            queries = Query.query.filter_by(conversation_id=conversation_id).all()
            conversation.contact = False
            db.session.commit()
            return jsonify({'conversation': conversation, 'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error updating conversation'}), 400
    return jsonify({'error':'Invalid request type'}), 400

@app.route('/queries/', methods=['GET'])
@cross_origin()
@token_required
def getAllQueries(user):
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
@token_required
def getUnresolvedQueries(user):
    if request.method  == 'GET':
        try:
            queries = Query.query.filter_by(resolved=False).all()
            print('Unresolved Queries: ', queries)
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching all queries'}), 400

    return jsonify({'error':'Invalid request type'}), 400



@app.route('/stats', methods=['GET'])
@cross_origin()
@token_required
def getStats(user):
    if request.method  == 'GET':
        try:
            convoCount = db.session.query(func.count(Conversation.id)).scalar() 
            queryCount = db.session.query(func.count(Query.id)).scalar()

            pendingCount = getCount(Conversation.query.filter(Conversation.contact==True))
            resolvedQueriesCount = getCount(Query.query.filter(Query.resolved ==True))
            accuracy = round((resolvedQueriesCount/queryCount) * 100)
            conversations = Conversation.query.order_by(Conversation.date).all()
            firstDate = conversations[0].date
            currentDate = datetime.now()
            delta = currentDate - firstDate
            numDays = delta.days
            averageConvosDaily = round(convoCount/numDays)
            
            print(pendingCount, resolvedQueriesCount)

            return jsonify({'conversations': {
                'total': convoCount,
                'dailyAverage': averageConvosDaily,
                'pending': pendingCount
            }, 'queries': {
                'total': queryCount, 
                'accuracy': accuracy,
                'unresolved': queryCount - resolvedQueriesCount
            }})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching statistics'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@app.route('/stats/date', methods=['GET'])
@cross_origin()
@token_required
def getStatsByDate(user):
    if request.method  == 'GET':
        try:
            year = request.args.get('year')
            month = request.args.get('month')
            day = request.args.get('day')
            print(year, month, day)
            startDate  = datetime(year=int(year), month = int(month), day=int(day)) 
            print(startDate)
            conversations = Conversation.query.filter(Conversation.date >= startDate )
            queries = Query.query.join(Conversation).filter(Conversation.date >= startDate)
            convoCount = getCount(conversations)
            queryCount = getCount(queries)
            pendingCount = getCount(conversations.filter(Conversation.contact==True))

            resolvedQueriesCount = getCount(queries.filter(Query.resolved ==True))
            accuracy = round((resolvedQueriesCount/queryCount) * 100)
            conversations = conversations.order_by(Conversation.date).all()
            firstDate = conversations[0].date
            currentDate = datetime.now()
            delta = currentDate - firstDate
            numDays = delta.days
            averageConvosDaily = round(convoCount/numDays)
            
            print("COUNT: ", convoCount)
            print("QUERY COUNT: ", queryCount)
            print(pendingCount, resolvedQueriesCount)
        
            return jsonify({'conversations': {
                'total': convoCount,
                'dailyAverage': averageConvosDaily,
                'pending': pendingCount
            }, 'queries': {
                'total': queryCount, 
                'accuracy': accuracy,
                'unresolved': queryCount - resolvedQueriesCount
            }})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching statistics'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/stats/daterange', methods=['GET'])
@cross_origin()
@token_required
def getStatsByDateRange(user):
    if request.method == 'GET':
        try:
            startYear = request.args.get('startYear')
            startMonth = request.args.get('startMonth')
            startDay = request.args.get('startDay')
            endYear = request.args.get('endYear')
            endMonth = request.args.get('endMonth')
            endDay = request.args.get('endDay')
            startDate  = datetime(year=int(startYear), month = int(startMonth), day=int(startDay))
            endDate = datetime(year=int(endYear), month=int(endMonth), day=int(endDay))
            print(startDate, endDate)
        
            conversations = Conversation.query.filter(Conversation.date.between(startDate, endDate))
            queries = Query.query.join(Conversation).filter(Conversation.date.between(startDate, endDate))
            convoCount = getCount(conversations)
            queryCount = getCount(queries)
            pendingCount = getCount(conversations.filter(Conversation.contact==True))
            resolvedQueriesCount = getCount(queries.filter(Query.resolved ==True))
            accuracy = round((resolvedQueriesCount/queryCount) * 100)
            conversations = conversations.order_by(Conversation.date).all()
            firstDate = conversations[0].date
            currentDate = datetime.now()
            delta = currentDate - firstDate
            numDays = delta.days
            print(numDays)
            if numDays == 0:
                numDays = 1
            averageConvosDaily = round(convoCount/numDays)
         
        
            return jsonify({'conversations': {
                'total': convoCount,
                'dailyAverage': averageConvosDaily,
                'pending': pendingCount
            }, 'queries': {
                'total': queryCount, 
                'accuracy': accuracy,
                'unresolved': queryCount - resolvedQueriesCount
            }})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching statistics'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@app.route('/stats/chart', methods=['GET'])
@cross_origin()
@token_required
def getChartData(user):
    if request.method == 'GET':
        try:
            
            startDate = datetime.today().replace(day=1)
            currentDate = datetime.today().strftime("%d") 
            conversations = Conversation.query.filter(Conversation.date >= startDate)
            dayCounts = dict()
            for i in range(1, int(currentDate) + 1):
                dayCounts[i] = 0
            for c in conversations:
                print(c.date)
                dayOfMonth = c.date.strftime("%d")
                print(dayOfMonth)

                dayCounts[int(dayOfMonth)] +=1 
                
            print(dayCounts)
            result = []
            for (day, count) in dayCounts.items():
                result.append({
                    'day': day,
                    'conversations': count
                })

            result.sort(key=lambda x: x['day'])

            return jsonify(result)
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching chart data'}), 400

    return jsonify({'error':'Invalid request type'}), 400

def getCount(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count


    return response
if __name__ == "__main__":
    app.run()