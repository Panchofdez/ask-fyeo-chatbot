from dataclasses import asdict
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from chatbot.chatbot_interface import ChatbotInterface
from .database import db, FAQ
from .helpers import formatFAQ
from .routes import routes
from .commands import faq_init, train_model, chat, view_intents
from enums import Mode

# app.config['CORS_HEADERS'] = 'Content-Type'
migrate = Migrate()
cors = CORS()

def create_app(mode=Mode.DEV, init=False):
    app = Flask(__name__)
    CORS(app)
    if mode == Mode.PROD:
    #database string needs to start with postgresql:// not postgres:// which is what heroku sets it to by default and is unchangeable
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)
        app.debug = False
    else:
        load_dotenv() #load environment variables for local environment
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:SpicyP#13@localhost/ask-fyeo-chatbot'
        app.debug = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('MY_SECRET_KEY')

    db.init_app(app)    
    cors.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():

        if init: 
            db.create_all()
        else:
            data = get_data()
            chatbot = ChatbotInterface(type=ChatbotInterface.bow_model, data=data, mode=mode)
            app.config["chatbot"] = chatbot

    
    app.register_blueprint(routes, url_prefix='')
    app.cli.add_command(faq_init)
    app.cli.add_command(train_model)
    app.cli.add_command(chat)
    app.cli.add_command(view_intents)

    return app 





#Model Setup
#get data to pass into chatbot model
def get_data():
    faqs = FAQ.query.order_by(FAQ.tag).all()
    faqs = list(map(formatFAQ, map(asdict, faqs)))
    print(len(faqs))
    return {"intents":faqs}


