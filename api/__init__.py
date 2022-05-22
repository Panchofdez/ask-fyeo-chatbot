from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from chatbot.chatbot_interface import ChatbotInterface
from .database import db
from .routes import routes
from .commands import backup_faq, faq_init, train_model, chat, view_intents, test_model, backup_faq, get_data, initialize_faq, initialize_staff_user
from enums import Mode

# app.config['CORS_HEADERS'] = 'Content-Type'
migrate = Migrate()
cors = CORS()

def create_app(mode=Mode.PROD, init=False):
    app = Flask(__name__)
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
            #initialize the tables in postgres
            db.create_all()
            initialize_faq()
            initialize_staff_user()
        else:
            data = get_data()
            chatbot = ChatbotInterface(type=ChatbotInterface.bert_model, data=data, mode=Mode.DEV)
            app.config["chatbot"] = chatbot

    
    app.register_blueprint(routes, url_prefix='')
    app.cli.add_command(faq_init)
    app.cli.add_command(train_model)
    app.cli.add_command(chat)
    app.cli.add_command(view_intents)
    app.cli.add_command(test_model)
    app.cli.add_command(backup_faq)

    return app 






