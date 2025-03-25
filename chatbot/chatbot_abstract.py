
from abc import ABC, abstractmethod

class Chatbot(ABC):

    @abstractmethod    
    def train(self):
        pass

    @abstractmethod    
    def get_response(self):
        pass

    @abstractmethod
    def chat(self):
        pass
