#run this script to train the desired chatbot
from api import create_app

def train():
    myapp = create_app()
    myapp.config["chatbot"].train()

