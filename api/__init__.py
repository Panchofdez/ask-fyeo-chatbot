from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from chatbot.chatbot_interface import ChatbotInterface
from .database import db, FAQ, Staff
from .routes import routes
from .commands import backup_faq, train_model, chat, view_intents, test_model, backup_faq, get_data
from enums import Mode
import json
from flask_apscheduler import APScheduler
from github import Github, Auth
import datetime

# app.config['CORS_HEADERS'] = 'Content-Type'
migrate = Migrate()
cors = CORS()


def create_app(mode=Mode.PROD,chatbot_mode=Mode.PROD,chatbot_type=ChatbotInterface.bow_model,init=False):
    app = Flask(__name__)

    if mode == Mode.PROD:
        #database string needs to start with postgresql:// not postgres:// which is what heroku sets it to by default and is unchangeable 
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("://", "ql://", 1)
        app.debug = False
    else:
        load_dotenv() #load environment variable
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL_DEV')#'postgresql://postgres:SpicyP#13@localhost/ask-fyeo-chatbot'
        app.debug = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('MY_SECRET_KEY')
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }

    db.init_app(app)    
    cors.init_app(app)
    migrate.init_app(app, db)
    
    # initialize scheduler
    scheduler = APScheduler()
    scheduler.api_enabled = True
    scheduler.init_app(app)

    @scheduler.task("interval", id="update_streamlit_repo", days=1)
    def update_streamlit_repo():
        print("Updating README of chatbot streamlit repo")
        auth = Auth.Token(os.environ.get('GIT_TOKEN'))
        g = Github(auth=auth)
        repo = g.get_repo("Panchofdez/ask-fyeo-chatbot-streamlit")    
        readme = repo.get_contents("README.md")
        contents = readme.decoded_content.decode()
        if contents.find("UPDATED:") == -1:
            contents += f"\nUPDATED: {datetime.datetime.now()}"
        else:
            contents = contents.split("UPDATED:")[0] + f"\nUPDATED: {datetime.datetime.now()}"
    
        print(contents)    
 
        repo.update_file(readme.path, "Update Repo README", contents, readme.sha, branch="main")
        g.close()
     
    scheduler.start()
    
    with app.app_context():
        if not init:
            data = get_data()
            chatbot = ChatbotInterface(type=chatbot_type, data=data, mode=chatbot_mode)
            app.config["chatbot"] = chatbot
        else:
            #initialize the tables in postgres
            try:
                db.create_all()
                with open('intents.json', 'r', encoding='utf8') as f:
                    file_data = json.loads(f.read())
                    for q in file_data['intents']:
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

                new_staff = Staff(email="pancho.fernandez@ryerson.ca")
                db.session.add(new_staff)
                db.session.commit()
            except Exception as e:
                print("ERROR", e)
            

    
    app.register_blueprint(routes, url_prefix='')
    app.cli.add_command(train_model)
    app.cli.add_command(chat)
    app.cli.add_command(view_intents)
    app.cli.add_command(test_model)
    app.cli.add_command(backup_faq)

    return app 






