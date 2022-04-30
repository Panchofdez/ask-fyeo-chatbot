from .bow_chatbot import BOWChatbot
from .bert_chatbot import BERTChatbot
import torch
from enums import Mode


class ChatbotInterface():
    bert_model = "bert"
    bow_model = "bow"


    def __init__(self, type, data, mode, **kwargs):
        self.type = type
        self.data = data 
        #files that contain the saved state of our trained models
        if mode == Mode.DEV:
            bert_file = "bertmodel.pth"
            bow_file = "bowmodel.pth"
        else:
            bert_file = "https://fyeochatbotmodels.s3.us-east-2.amazonaws.com/bertmodel.pth"
            bow_file = "https://fyeochatbotmodels.s3.us-east-2.amazonaws.com/bowmodel.pth"
        if type == ChatbotInterface.bert_model:
            self.model = BERTChatbot(**kwargs)
            self.file = self.get_bertfile(bert_file)
        else:
            self.model = BOWChatbot(**kwargs)
            self.file = self.get_bowfile(bow_file)
        
     

    def train(self):
        self.model.train(self.data)
    

    def chat(self):
        self.model.chat(self.data, self.file)
      

    def get_response(self, question):
        try:
            return self.model.get_response(question, self.data, self.file)
        except Exception as e:
            return e

   

    def get_bertfile(self,f):
        file = torch.load(f)
        return file


    def get_bowfile(self, f):
        file = torch.load(f)
        return file
        
