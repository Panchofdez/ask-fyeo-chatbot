from .bow_chatbot import BOWChatbot
from .bert_chatbot import BERTChatbot
import torch
from enums import Mode
import io
from smart_open import open as smart_open


class ChatbotInterface():
    bert_model = "bert"
    bow_model = "bow"


    def __init__(self, type, data, mode, **kwargs):
        self.type = type
        self.data = data 
        #files that contain the saved state of our trained models
        if mode == Mode.DEV:
            bert_url = "bertmodel.pth"
            bow_url = "bowmodel.pth"
        else:
            bert_url = "https://fyeochatbotmodels.s3.us-east-2.amazonaws.com/bertmodel.pth"
            bow_url = "https://fyeochatbotmodels.s3.us-east-2.amazonaws.com/bowmodel.pth"
        if type == ChatbotInterface.bert_model:
            self.model = BERTChatbot(**kwargs)
            self.file = self.get_file(bert_url)
        else:
            self.model = BOWChatbot(**kwargs)
            self.file = self.get_file(bow_url)
        
     

    def train(self):
        self.model.train(self.data)
    

    def chat(self):
        self.model.chat(self.data, self.file)
      

    def get_response(self, question):
        try:
            return self.model.get_response(question, self.data, self.file)
        except Exception as e:
            return e

   

    def get_file(self,url):
        with smart_open(url, 'rb') as f:
            buffer = io.BytesIO(f.read())
            file = torch.load(buffer)
            return file


        
