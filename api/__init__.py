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
from .commands import create_tables, faq_init

# app.config['CORS_HEADERS'] = 'Content-Type'
PROD = "Prod"
DEV = "Dev"

def create_app(type=DEV):
    app = Flask(__name__)
    CORS(app)
    if type == PROD:
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
    migrate = Migrate(app, db)

    with app.app_context():
        data = get_data()
        chatbot = ChatbotInterface(type=ChatbotInterface.bert_model, data=data)
        app.config["chatbot"] = chatbot

    
    app.register_blueprint(routes, url_prefix='')
    app.cli.add_command(create_tables)
    app.cli.add_command(faq_init)

    return app 





#Model Setup
#get data to pass into chatbot model
def get_data():
    faqs = FAQ.query.order_by(FAQ.tag).all()
    faqs = list(map(formatFAQ, map(asdict, faqs)))
    print(len(faqs))
    return {"intents":faqs}







# if __name__ == "__main__":
#     app = create_app(DEV)
#     app.run()