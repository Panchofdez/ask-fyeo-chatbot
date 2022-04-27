#run this script to train the desired chatbot
from app import create_app

myapp = create_app()

myapp.config["chatbot"].chat()