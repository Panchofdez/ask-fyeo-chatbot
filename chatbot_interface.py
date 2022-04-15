from bow_chatbot import BOWChatbot
from helpers import formatFAQ
from dataclasses import asdict
from app import FAQ
from bert_chatbot import BERTChatbot
import torch



class ChatbotInterface():
    bert_model = "bert"
    bow_model = "bow"

    #files that contain the saved state of our trained models
    bert_file = "bertmodel.pth"
    bow_file = "bowmodel.pth"

    def __init__(self, type, **kwargs):
        self.data = self.get_data()
        self.type = type
        if type == ChatbotInterface.bert_model:
            self.model = BERTChatbot(**kwargs)
            self.file = self.get_bertfile()
        else:
            self.model = BOWChatbot(**kwargs)
            self.file = self.get_bowfile()
        

    def get_data(self):
        faqs = FAQ.query.order_by(FAQ.tag).all()
        faqs = list(map(formatFAQ, map(asdict, faqs)))
        print(len(faqs))
        return {"intents":faqs}

    def train(self):
        self.model.train(self.data)

    def chat(self):
        self.model.chat(self.data, self.file)

    def get_response(self, question):
        self.model.get_response(question, self.data, self.file)

    def get_bertfile(self):
        file = torch.load(ChatbotInterface.bert_file)
        return file

    def get_bowfile(self):
        file = torch.load(ChatbotInterface.bow_file)
        return file



chatbot = ChatbotInterface(ChatbotInterface.bert_model)
chatbot.chat()
