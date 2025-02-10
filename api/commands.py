from dataclasses import asdict
import click
from flask.cli import with_appcontext
from flask import  current_app
import json
from .helpers import formatFAQ
from .database import db, FAQ, Staff


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
            
@click.command(name='test_model')
@with_appcontext
def test_model():
    data = get_data()
    num_correct = 0
    num_questions = 0
    # print(data)
    for intent in data["intents"]:
        for question in intent["patterns"]:
            tag, response = current_app.config['chatbot'].get_response(question)
            if tag == intent["tag"]:
                num_correct +=1
            else:
                print("ERROR: ", question)
                print(f"Correct Tag: {intent['tag']} Receieved: {tag}")
                print(response)
                print()
            num_questions += 1

    accuracy = (num_correct/num_questions) * 100
    print(accuracy)
    return



@click.command(name='backup_faq')
@with_appcontext
def backup_faq():
    data = get_data()

    #remove the last_updated field as json does not store datetime objects
    data["intents"] = list(map(lambda x: {key:value for key, value in x.items() if key != 'last_updated'},  data["intents"])) 
    #print(data)
    with open("intents.json", "w") as outfile:
        json.dump(data, outfile,indent=4)



#Model Setup
#get data to pass into chatbot model
def get_data():
    faqs = FAQ.query.order_by(FAQ.tag).all()
    faqs = list(map(formatFAQ, map(asdict, faqs)))
    print("# FAQs: ", len(faqs))
    return {"intents":faqs}


#Initializes the faq with the pre-defined json file
def initialize_faq():
    with open('intents.json', 'r', encoding='utf8') as f:
        file_data = json.loads(f.read())
        for q in file_data['intents']:
            #print(q)
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

#set the initial staff member to access the management side of app. This user can then add more users
def initialize_staff_user():
    new_staff = Staff(email="pancho.fernandez@ryerson.ca")
    db.session.add(new_staff)
    db.session.commit()