import json
from nltk_utils import tokenize, stem, bag_of_words
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from model import NeuralNet
from app import FAQ
from helpers import formatFAQ
from dataclasses import asdict

class ChatDataset(Dataset):
    def __init__(self, X_train, y_train):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples


def train(intents):
    all_words = []
    tags = []
    xy = []
    ignore_words = ['?', '!', '.', ',']
    for intent in intents["intents"]:
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

    #Hyper-parameters
    batch_size = 8
    input_size = len(all_words)
    hidden_size = 8
    output_size = len(tags)
    learning_rate=0.001
    num_epochs = 1000

    dataset = ChatDataset(X_train=X_train, y_train=y_train)
    train_loader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=True, num_workers=0)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = NeuralNet(input_size, hidden_size, output_size).to(device)

    #loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    for epoch in range(num_epochs):
    
        for (words, labels) in train_loader:
            words = words.to(device)
            labels =  labels.to(device=device,dtype=torch.long)

            #forward propogation
            outputs = model(words)
            loss = criterion(outputs, labels)

            #backward prop and optimizer step
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        
        if (epoch + 1) % 100 == 0:
            
            print(f'epoch {epoch+1}/{num_epochs}, loss={loss.item():.10f}')


    print(f'final loss: loss={loss.item():.10f}')

    data = {
        "model_state":model.state_dict(),
        "input_size":input_size,
        "output_size": output_size,
        "hidden_size": hidden_size,
        "all_words": all_words,
        "tags": tags
    }


    FILE = "data.pth"
    torch.save(data, FILE)

    print(f"Training complete. File saved to {FILE}")

def getTrainingData():       
    faqs = FAQ.query.order_by(FAQ.tag).all()
    faqs = list(map(formatFAQ, map(asdict, faqs)))
    print(len(faqs))
    train({"intents" :faqs})


# with open("intents.json", "r", encoding="utf8") as f:
#     intents = json.load(f)

# train(intents)

getTrainingData()