from .bow_chatbot import BOWChatbot
from .bert_chatbot import BERTChatbot
import torch



class ChatbotInterface():
    bert_model = "bert"
    bow_model = "bow"

    #files that contain the saved state of our trained models
    bert_file = "chatbot/bertmodel.pth"
    bow_file = "chatbot/bowmodel.pth"

    def __init__(self, type, data, **kwargs):
        self.type = type
        self.data = data 
        if type == ChatbotInterface.bert_model:
            self.model = BERTChatbot(**kwargs)
            self.file = self.get_bertfile()
        else:
            self.model = BOWChatbot(**kwargs)
            self.file = self.get_bowfile()
        


    def train(self):
        self.model.train(self.data)
    

    def chat(self):
        self.model.chat(self.data, self.file)
      

    def get_response(self, question):
        try:
            return self.model.get_response(question, self.data, self.file)
        except Exception as e:
            return e

   

    def get_bertfile(self):
        try:
            file = torch.load(ChatbotInterface.bert_file)
            return file
        except FileNotFoundError as e:
            return None

    def get_bowfile(self):
        try:
            file = torch.load(ChatbotInterface.bow_file)
            return file
        except FileNotFoundError as e:
            return None

