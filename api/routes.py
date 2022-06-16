from flask import request, jsonify, Blueprint, current_app
from flask_cors import cross_origin
import functools
import os
from dataclasses import asdict
from datetime import datetime, timedelta
from sqlalchemy.sql.functions import func
import jwt 
from functools import wraps
from .helpers import getCount, formatFAQ, addFAQStats
from .database import db, Conversation, Query, Staff, FAQ


routes = Blueprint('routes', __name__)

def token_required(func):
    '''Decorator that acts as a middleware to check if a user is signed before accessing route'''
    @wraps(func)
    def inner(*args, **kwargs):
        auth_header = request.headers.get('authorization')
        user= None
        print("header", auth_header)
        if auth_header:
            token = auth_header.replace("Bearer ", "")
            try:
                data = jwt.decode(token, current_app.config['SECRET_KEY'],  algorithms=["HS256"])
                user = Staff.query.filter_by(email=data['email']).first()
                print("User", user)
            except Exception as e:
                print("ERROR in getting user: ", e)
                return jsonify({'error':'Not Authorized'}), 403
        else:
            return jsonify({'error':'Not Authorized'}), 401
        return func(user, *args, **kwargs)
    return inner

@routes.route('/')
@cross_origin()
def hello():
    return 'Hello World'


@routes.route('/login', methods=['POST'])
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
            token = jwt.encode({'email': user.email,'exp' : datetime.utcnow() + timedelta(minutes=45)},  current_app.config['SECRET_KEY'], algorithm="HS256")

            print(token)

            return jsonify({'token': token})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error logging in'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/staff', methods=['GET'])
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

@routes.route('/staff', methods=['POST'])
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


@routes.route('/staff/<id>', methods=['DELETE'])
@cross_origin()
@token_required
def removeStaff(user, id):
    print("hello")
    if request.method == 'DELETE':
        try:
            
            staffMember = Staff.query.get(id)
            print(staffMember)
            if user.email == staffMember.email:
                return jsonify({'error':"Can't remove yourself from staff access"}), 400
            
            db.session.delete(staffMember)
            db.session.commit()
            all_staff = Staff.query.all()
            return jsonify({'staff': all_staff })
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error removing staff member'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/chat/start', methods=['POST'])
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

@routes.route('/chat/answer', methods=['POST'])
@cross_origin()
def predict():
    if request.method == 'POST':
        try:
            print("Hello")
            conversation_id = request.json['conversation_id']
            question = request.json['question']
            print(question, conversation_id)
            tag, response = current_app.config["chatbot"].get_response(question)
            print(response)
            conversation = Conversation.query.get(conversation_id)
            faq = FAQ.query.filter(FAQ.tag == tag).first()
            if faq == None:
                query = Query(question=question, response=response, conversation_id=conversation.id)
            else:
                query = Query(question=question, response=response, conversation_id=conversation.id, faq_id=faq.id)

            db.session.add(query)
            db.session.commit()
            print('RESPONSE ', response)
            return jsonify({ 'query': query})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in providing chatbot response'}), 400

    return jsonify({'error':'Invalid request type'}), 400



@routes.route('/chat/resolve', methods=['PUT'])
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
            return jsonify({'error':'Error in setting conversation status'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/chat/contact', methods=['PUT'])
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
            return jsonify({'error':'Error in setting contact status'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/conversations', methods=['GET'])
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
                resolved_queries = Query.query.filter_by(conversation_id=convoDict['id'] , resolved=True).all()
                convoDict['resolved'] = len(resolved_queries)
                response.append(convoDict)
        
            return jsonify({'conversations': response})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching all conversations'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/conversations/date', methods=['GET'])
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
                resolved_queries = Query.query.filter_by(conversation_id=convoDict['id'] , resolved=True).all()
                convoDict['resolved'] = len(resolved_queries)
                response.append(convoDict)
        
            return jsonify({'conversations': response})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching conversations by date'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/conversations/daterange', methods=['GET'])
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
                resolved_queries = Query.query.filter_by(conversation_id=convoDict['id'] , resolved=True).all()
                convoDict['resolved'] = len(resolved_queries)
                response.append(convoDict)
        
            return jsonify({'conversations': response})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error in fetching conversations by date range'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/conversations/<conversation_id>', methods=['GET'])
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


@routes.route('/conversation/<conversation_id>', methods=['PUT'])
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
            print("Convo: ", conversation)
            return jsonify({'conversation': conversation, 'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error updating conversation'}), 400
    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/queries', methods=['GET'])
@cross_origin()
@token_required
def getQueries(user):
    if request.method  == 'GET':
        try:
            queries = Query.query.join(Conversation).order_by(Conversation.date.desc()).all()
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching all queries'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/queries/unresolved', methods=['GET'])
@cross_origin()
@token_required
def getUnresolvedQueries(user):
    if request.method  == 'GET':
        try:
            queries = Query.query.join(Conversation).filter_by(resolved=False).order_by(Conversation.date.desc()).all()
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching all unresolved queries'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/queries/date', methods=['GET'])
@cross_origin()
@token_required
def getQueriesByDate(user):
    if request.method  == 'GET':
        try:
            year = request.args.get('year')
            month = request.args.get('month')
            day = request.args.get('day')
            print(year, month, day)
            startDate  = datetime(year=int(year), month = int(month), day=int(day)) 
            print(startDate)
            queries = Query.query.join(Conversation).filter(Conversation.date >= startDate).order_by(Conversation.date.desc()).all()
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching queries by date'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/queries/daterange', methods=['GET'])
@cross_origin()
@token_required
def getQueriesByDateRange(user):
    if request.method  == 'GET':
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
            queries = Query.query.join(Conversation).filter(Conversation.date.between(startDate, endDate)).order_by(Conversation.date.desc()).all()
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching queries by date range'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/stats', methods=['GET'])
@cross_origin()
@token_required
def getStats(user):
    if request.method  == 'GET':
        try:
            convoCount = db.session.query(func.count(Conversation.id)).scalar() 
            queryCount = db.session.query(func.count(Query.id)).scalar()
            pendingCount = getCount(Conversation.query.filter(Conversation.contact==True))
            resolvedQueriesCount = getCount(Query.query.filter(Query.resolved ==True))
            conversations = Conversation.query.order_by(Conversation.date).all()
            
            if queryCount == 0:
                accuracy = 0
                averageConvosDaily = 0
            else:
                accuracy = round((resolvedQueriesCount/queryCount) * 100)
                firstDate = conversations[0].date
                currentDate = datetime.now()
                delta = currentDate - firstDate
                numDays = delta.days

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


@routes.route('/stats/date', methods=['GET'])
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

            if queryCount == 0:
                accuracy = 0
                averageConvosDaily = 0
            else:
                accuracy = round((resolvedQueriesCount/queryCount) * 100)
                conversations = conversations.order_by(Conversation.date).all()
                firstDate = conversations[0].date
                currentDate = datetime.now()
                delta = currentDate - firstDate
                numDays = delta.days

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

@routes.route('/stats/daterange', methods=['GET'])
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
            conversations = conversations.order_by(Conversation.date).all()

            if queryCount == 0:
                accuracy = 0
                averageConvosDaily = 0
            else:
                accuracy = round((resolvedQueriesCount/queryCount) * 100)    
                firstDate = conversations[0].date
                currentDate = datetime.now()
                delta = currentDate - firstDate
                numDays = delta.days
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

@routes.route('/stats/chart', methods=['GET'])
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



@routes.route('/faq', methods=['GET'])
@cross_origin()
@token_required
def getFAQ(user):
    if request.method == 'GET':
        try:
            faqs = FAQ.query.order_by(FAQ.tag).all()
            unidentified_queries = Query.query.filter(Query.faq_id == None).all()
            num_total_queries = functools.reduce(lambda acc, f: acc + len(f.queries),faqs, 0) + len(unidentified_queries)
            
            print(num_total_queries)
            faqs = addFAQStats(faqs, unidentified_queries, num_total_queries)
          
            return jsonify({"FAQ": faqs})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching FAQ'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/faq', methods=['POST'])
@cross_origin()
@token_required
def addFAQ(user):
    if request.method == 'POST':
        try:
            tag = request.json['tag']
            patterns = request.json['patterns']
            responses = request.json['responses']

            if len(list(filter(lambda p: p.find('|') != -1, patterns))) > 0 or len(list(filter(lambda r: r.find('|') != -1, responses))) > 0:
                return jsonify({'error':'Error adding FAQ, Invalid character "|" found'}), 400

            patterns = '|'.join(patterns)
            responses = '|'.join(responses)

            if len(FAQ.query.filter(FAQ.tag==tag).all()) > 0:
                return jsonify({'error':'Error adding FAQ, Tag must be unique'}), 400

            new_faq = FAQ(tag=tag, patterns=patterns, responses=responses, last_updated=datetime.now())
            db.session.add(new_faq)
            db.session.commit()

            faqs = FAQ.query.order_by(FAQ.tag).all()
            faqs = list(map(formatFAQ, map(asdict,faqs)))
            return jsonify({"FAQ": faqs})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error adding FAQ'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/faq/all', methods=['POST'])
@cross_origin()
@token_required
def addAllFAQ(user):
    if request.method == 'POST':
        try:
            faq = request.json['faq']
            
            for q in faq:
                tag = q['tag']
                patterns = q['patterns']
                responses = q['responses']

                if len(list(filter(lambda p: p.find('|') != -1, patterns))) > 0 or len(list(filter(lambda r: r.find('|') != -1, responses))) > 0:
                    return jsonify({'error':'Error adding FAQ, Invalid character "|" found'}), 400

                patterns = '|'.join(patterns)
                responses = '|'.join(responses)

                if len(FAQ.query.filter(FAQ.tag==tag).all()) > 0:
                    return jsonify({'error':'Error adding FAQ, Tag must be unique'}), 400

                new_faq = FAQ(tag=tag, patterns=patterns, responses=responses, last_updated=datetime.now())
                db.session.add(new_faq)
           
            db.session.commit()
            faqs = FAQ.query.order_by(FAQ.tag).all()
            faqs = list(map(formatFAQ, map(asdict, faqs)))
            return jsonify({"FAQ": faqs})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error adding FAQ'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/faq', methods=['PUT'])
@cross_origin()
@token_required
def updateFAQ(user):
    if request.method == 'PUT':
        try:
            tag = request.json['tag']
            patterns = request.json['patterns']
            responses = request.json['responses']

            if len(list(filter(lambda p: p.find('|') != -1, patterns))) > 0 or len(list(filter(lambda r: r.find('|') != -1, responses))) > 0:
                return jsonify({'error':'Error adding FAQ, Invalid character "|" found'}), 400

            patterns = '|'.join(patterns)
            responses = '|'.join(responses)
            print("Date", datetime.now())
            current_faq = FAQ.query.filter(FAQ.tag == tag).first()
            current_faq.patterns = patterns
            current_faq.responses = responses
            current_faq.last_updated = datetime.now()
            db.session.commit()

            faqs = FAQ.query.order_by(FAQ.tag).all()
            faqs = list(map(formatFAQ, map(asdict, faqs)))

            return jsonify({"FAQ": faqs})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error updating FAQ'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/faq/<faq_id>', methods=['DELETE'])
@cross_origin()
@token_required
def deleteFAQ(user, faq_id):
    if request.method == 'DELETE':
        try:
            print(faq_id) 
            faq = FAQ.query.get(faq_id)
            
            db.session.delete(faq)
            db.session.commit()

            faqs = FAQ.query.order_by(FAQ.tag).all()
            faqs = list(map(formatFAQ, map(asdict, faqs)))

            return jsonify({"FAQ": faqs})
        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error deleting FAQ'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/faq/<faq_id>/queries', methods=['GET'])
@cross_origin()
@token_required
def getFAQQueries(user, faq_id):
    if request.method  == 'GET':
        try:
            if int(faq_id) < 0 :
                faq_id = None
            queries = Query.query.join(Conversation).filter(Query.faq_id == faq_id).order_by(Conversation.date.desc()).all()
  
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching all queries'}), 400

    return jsonify({'error':'Invalid request type'}), 400


@routes.route('/faq/<faq_id>/queries/date', methods=['GET'])
@cross_origin()
@token_required
def getFAQQueriesByDate(user, faq_id):
    if request.method  == 'GET':
        try:
            if int(faq_id) < 0 :
                faq_id = None
            year = request.args.get('year')
            month = request.args.get('month')
            day = request.args.get('day')
            print(year, month, day)
            startDate  = datetime(year=int(year), month = int(month), day=int(day)) 
            print(startDate)
            queries = Query.query.join(Conversation).filter(Query.faq_id == faq_id).filter(Conversation.date >= startDate).order_by(Conversation.date.desc()).all()
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching queries by date'}), 400

    return jsonify({'error':'Invalid request type'}), 400

@routes.route('/faq/<faq_id>/queries/daterange', methods=['GET'])
@cross_origin()
@token_required
def getFAQQueriesByDateRange(user, faq_id):
    if request.method  == 'GET':
        try:
            if int(faq_id) < 0 :
                faq_id = None
            startYear = request.args.get('startYear')
            startMonth = request.args.get('startMonth')
            startDay = request.args.get('startDay')
            endYear = request.args.get('endYear')
            endMonth = request.args.get('endMonth')
            endDay = request.args.get('endDay')
            startDate  = datetime(year=int(startYear), month = int(startMonth), day=int(startDay))
            endDate = datetime(year=int(endYear), month=int(endMonth), day=int(endDay))
            print(startDate, endDate)
            queries = Query.query.join(Conversation).filter(Query.faq_id == faq_id).filter(Conversation.date.between(startDate, endDate)).order_by(Conversation.date.desc()).all()
            return jsonify({'queries': queries})

        except Exception as e:
            print("Error: ", e)
            return jsonify({'error':'Error fetching queries by date range'}), 400

    return jsonify({'error':'Invalid request type'}), 400
