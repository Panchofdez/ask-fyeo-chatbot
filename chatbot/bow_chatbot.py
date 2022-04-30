import torch
import torch.nn as nn
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from .chatbot_abstract import Chatbot
from .nltk_utils import tokenize, stem, bag_of_words
import re



'''Chatbot using Bag-of-words technique and a deep learning model 
based on the article: https://chatbotsmagazine.com/contextual-chat-bots-with-tensorflow-4391749d0077''' 
class BOWChatbot(Chatbot):

    def __init__(self, batch_size = 8, learning_rate=0.001, epochs=1000 ):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        #Hyper-parameters
        self.batch_size = batch_size
        self.learning_rate=learning_rate
        self.epochs = epochs


    def train(self,data):
        all_words = []
        tags = []
        xy = []
        ignore_words = ['?', '!', '.', ',']
        for intent in data["intents"]:
            tag = intent["tag"]
            tags.append(tag)
            for pattern in intent["patterns"]:
                w = tokenize(pattern)
                all_words.extend(w)
                xy.append((w, tag))

        all_words = [stem(w) for w in all_words if w not in ignore_words]
        all_words = sorted(set(all_words))
        tags = sorted(set(tags))

        print(len(xy), "patterns")
        print(len(tags), "tags:", tags)
        print(len(all_words), "unique stemmed words:", all_words)

        X_train = []
        y_train = []

        for (pattern_sentence, tag) in xy:
            bag  = bag_of_words(pattern_sentence, all_words)
            X_train.append(bag)

            label = tags.index(tag)
            y_train.append(label)

        print(bag)

        X_train = np.array(X_train)
        y_train = np.array(y_train)
        print(X_train)
        print(y_train)

        input_size = len(all_words)
        output_size = len(tags) 
        hidden_size = 64

        dataset = ChatDataset(X_train=X_train, y_train=y_train)
        train_loader = DataLoader(dataset=dataset, batch_size=self.batch_size, shuffle=True, num_workers=0)

        model = NeuralNet(input_size, hidden_size, output_size).to(self.device)

        #loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=self.learning_rate)

        for epoch in range(self.epochs):
        
            for (words, labels) in train_loader:
                words = words.to(self.device)
                labels =  labels.to(device=self.device,dtype=torch.long)

                #forward propogation
                outputs = model(words)
                loss = criterion(outputs, labels)

                #backward prop and optimizer step
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

            
            if (epoch + 1) % 100 == 0:
                
                print(f'epoch {epoch+1}/{self.epochs}, loss={loss.item():.10f}')


        print(f'final loss: loss={loss.item():.10f}')

        data = {
            "model_state":model.state_dict(),
            "input_size":input_size,
            "output_size": output_size,
            "hidden_size": hidden_size,
            "all_words": all_words,
            "tags": tags
        }
        FILE = "bowmodel.pth"
        torch.save(data, FILE)
        print(f"Training complete. File saved to {FILE}")

    def classify(self, sentence, model, all_words, tags):
        X = bag_of_words(sentence, all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X)

        output = model(X)
        print("output", output)
        _, predicted = torch.max(output, dim=1)
        tag = tags[predicted.item()]
        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]
        results = [ (i, p) for i, p in enumerate(probs.detach().numpy()[0])  if p > 0.5]
        results.sort(key=lambda x: x[1], reverse=True)
        print(results)
        return_list = []
        for r in results:
            return_list.append((tags[r[0]], r[1]))

        return return_list

    def get_response(self,sentence, data, file):     
        tokenized_sentence = tokenize(sentence)
        model_state=file["model_state"]
        input_size=file["input_size"]
        hidden_size=file["hidden_size"]
        output_size=file["output_size"]
        all_words=file["all_words"]
        tags=file["tags"]

        model = NeuralNet(input_size, hidden_size, output_size).to(self.device)
        model.load_state_dict(model_state)
        model.eval()
        results = self.classify(tokenized_sentence, model, all_words, tags )
        print("FINAL RESULTS: ",results)
        while results:
            for intent in data["intents"]:
                if results[0][0] == intent["tag"]:
                    resp = random.choice(intent['responses'])
                    if self.check_response(intent["tag"], sentence, resp):
                        return  (intent["tag"], f"{resp}")
            results.pop(0) 

        return ("" , "I do not understand please try again or ask another question ... ")


    def chat(self, data, file):
        bot_name = "Sam"
        print("let's chat: type 'quit' to exit")
        while True:
            sentence = input('You: ')
            if sentence == "quit":
                break

            print(f"{bot_name} {self.get_response(sentence, data, file)[1]}")

    def check_response(self,t,  q, r):
        '''
        Determines the validity of the chatbot's response
        '''
        q = tokenize(q)

        ignore_words = ['?', '!', '.', ',', 'are', 'you', 'can', 'and', 'you', 'let', ]
        stemmed_words  = [stem(w) for w in q if w not in ignore_words and len(w) > 2 ] # avoid punctuation or words like I , a , or 
        print(stemmed_words)
        found = [ w for w in stemmed_words if re.search(w, r) != None or re.search(w,t.lower() ) != None] #check if the question has words related in the response
        print(found)
        return len(found) > 0

class NeuralNet(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        #set up the layers of nn

        super(NeuralNet, self).__init__()
        self.l1 = nn.Linear(input_size, hidden_size)
        self.l2 = nn.Linear(hidden_size, hidden_size)
        self.l3 = nn.Linear(hidden_size, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        #apply activation functions to each layer
        out = self.l1(x)
        out = self.relu(out)
        out = self.l2(out)
        out = self.relu(out)
        out = self.l3(out)
        return out



class ChatDataset(Dataset):
    def __init__(self, X_train, y_train):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples


